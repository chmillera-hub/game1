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

  const now = () => (root.performance ? root.performance.now() : Date.now());
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
      this.computeLayout();
      this.staticDirty = true;
    }

    resize(cssW, cssH) {
      const dpr = Math.min(root.devicePixelRatio || 1, 3);
      if (cssW === this.cssW && cssH === this.cssH && dpr === this.dpr) return;
      this.dpr = dpr;
      this.cssW = Math.max(1, cssW);
      this.cssH = Math.max(1, cssH);
      this.cv.width = Math.round(this.cssW * dpr);
      this.cv.height = Math.round(this.cssH * dpr);
      this.cv.style.width = this.cssW + 'px';
      this.cv.style.height = this.cssH + 'px';
      this.computeLayout();
      this.staticDirty = true;
    }

    computeLayout() {
      const W = this.w;
      const H = this.h;
      const span = (W + H) / 2;
      const ratio = 0.5;
      const depth = 0.17;
      const head = 0.92;
      const foot = 0.1;
      const base = Math.max(8, Math.min((this.cssW - 6) / span, (this.cssH - 4) / (span * ratio + depth + head + foot)));
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
      const top = (this.cssH - total) / 2 + head * tw;
      this.clampPan();
      this.ox = this.cssW / 2 - ((W - H) * tw) / 4 + this.panX;
      this.oy = top + this.th / 2 + this.panY;
    }

    clampPan() {
      const mx = Math.max(0, (this.boardW - this.cssW) / 2 + this.tw * 0.5);
      const my = Math.max(0, (this.boardTotalH - this.cssH) / 2 + this.tw * 0.4);
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

    centerOn(x, y) {
      if (this.zoom <= 1) return;
      const [sx, sy] = this.center(x, y);
      this.panBy(this.cssW / 2 - sx, this.cssH * 0.55 - sy);
    }

    center(x, y) {
      return [this.ox + ((x - y) * this.tw) / 2, this.oy + ((x + y) * this.th) / 2];
    }

    toGrid(px, py) {
      const dx = (px - this.ox) / (this.tw / 2);
      const dy = (py - this.oy) / (this.th / 2);
      return [(dx + dy) / 2, (dy - dx) / 2];
    }

    tileAt(px, py) {
      const [fx, fy] = this.toGrid(px, py);
      const x = Math.round(fx);
      const y = Math.round(fy);
      if (x < 0 || y < 0 || x >= this.w || y >= this.h) return null;
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
          if (this.onLongPress) this.onLongPress(this.hit(tap.x, tap.y));
        }, 480);
      });
      this.cv.addEventListener('pointermove', (e) => {
        if (!pts.has(e.pointerId)) return;
        const [x, y] = pos(e);
        pts.set(e.pointerId, { x, y });
        if (pinch && pts.size >= 2) {
          const [a, b] = [...pts.values()];
          const d = Math.hypot(a.x - b.x, a.y - b.y) || 1;
          this.setZoom(pinch.z * (d / pinch.d), (a.x + b.x) / 2, (a.y + b.y) / 2);
          return;
        }
        if (!tap) return;
        if (!tap.panning && Math.hypot(x - tap.x, y - tap.y) > 10) {
          clearTimeout(timer);
          this.ov.press = null;
          if (this.zoom > 1) tap.panning = true;
          else {
            tap = null;
            return;
          }
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
          const [x, y] = pos(e);
          this.setZoom(this.zoom * (e.deltaY < 0 ? 1.12 : 1 / 1.12), x, y);
        },
        { passive: false }
      );
    }

    // What a tap at (px, py) points at: the tile under the finger and any unit sprite there.
    hit(px, py) {
      const tile = this.tileAt(px, py);
      let unitTile = null;
      const list = [...this.vis.values()].filter((v) => v.alpha > 0.3).sort((a, b) => b.x + b.y - (a.x + a.y) || b.x - a.x);
      for (const v of list) {
        const [cx, cy] = this.center(v.x, v.y);
        const hgt = (S.HEIGHT[v.type] || 40) * this.unit * (v.scale || 1);
        const half = this.tw * 0.3;
        if (px >= cx - half && px <= cx + half && py <= cy + this.th * 0.35 && py >= cy - hgt) {
          unitTile = { x: Math.round(v.x), y: Math.round(v.y), uid: v.uid };
          break;
        }
      }
      return { tile, unitTile, px, py, grid: this.toGrid(px, py) };
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
        v.para = u.para;
        v.poison = !!u.poison;
        v.rank = u.rank;
        v.activated = u.activated;
        v.alpha = v.dying ? v.alpha : 1;
      }
      for (const uid of [...this.vis.keys()]) if (!seen.has(uid) && !(opts && opts.keep)) this.vis.delete(uid);
    }

    makeVis(u) {
      return {
        uid: u.uid, type: u.type, team: u.team, x: u.x, y: u.y, facing: u.facing, hp: u.hp, maxHp: u.maxHp,
        wait: u.wait || 0, para: u.para || 0, poison: !!u.poison, rank: u.rank || 1, boss: !!u.boss, vip: !!u.vip,
        nonCombat: !!u.nonCombat, alpha: 1, ox: 0, oy: 0, hop: 0, scale: 1, shake: 0, flash: 0,
        phase: (u.uid * 1.7) % 6.28, activated: !!u.activated, ghost: !!u.ghost, rid: u.rid,
      };
    }

    clearUnits() {
      this.vis.clear();
      this.fx = [];
      this.texts = [];
    }

    // Loot on the field and the shrine to hold, if the mission has them.
    setObjectives(loot, hold) {
      this.loot = (loot || []).map((l) => Object.assign({}, l));
      this.hold = hold ? Object.assign({ count: 0 }, hold) : null;
    }

    // ---------------------------------------------------------- loop

    start() {
      if (this.running) return;
      this.running = true;
      this.last = now();
      const loop = () => {
        if (!this.running) return;
        this.frame();
        this.raf = requestAnimationFrame(loop);
      };
      this.raf = requestAnimationFrame(loop);
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
      this.drawObjects(g);
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
      if (this.hold) this.drawHold(g);
      if (o.deploy)
        for (const [x, y] of o.deploy) this.tileFill(g, x, y, 'rgba(90,160,255,0.16)', 'rgba(150,200,255,0.55)', 3, 1);
      if (o.danger)
        for (const [x, y, lvl] of o.danger) this.tileFill(g, x, y, lvl > 1 ? 'rgba(200,60,220,0.2)' : 'rgba(230,50,40,0.22)', null, 1);
      if (o.range) for (const [x, y] of o.range) this.tileFill(g, x, y, 'rgba(255,90,70,0.12)', 'rgba(255,120,100,0.3)', 3, 1);
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

    drawLootItem(g, l) {
      const [cx, cy] = this.center(l.x, l.y);
      g.save();
      g.translate(cx, cy);
      g.scale(this.unit, this.unit);
      S.ellipse(g, 0, 1, 12, 5, 'rgba(0,0,0,0.25)', 0);
      S.drawLoot(g, l.kind, this.time);
      g.restore();
    }

    // ---------------------------------------------------------- objects (units + obstacles)

    drawObjects(g) {
      const items = [];
      for (let y = 0; y < this.h; y++)
        for (let x = 0; x < this.w; x++) if (this.terrain[y * this.w + x] === 1) items.push({ k: x + y, x, obstacle: true, y });
      for (const v of this.vis.values()) items.push({ k: v.x + v.y + 0.01, x: v.x, v });
      for (const l of this.loot) if (!l.taken) items.push({ k: l.x + l.y, x: l.x, loot: l });
      items.sort((a, b) => a.k - b.k || a.x - b.x);
      const bars = [];
      for (const it of items) {
        if (it.obstacle) this.drawObstacle(g, it.x, it.y);
        else if (it.loot) this.drawLootItem(g, it.loot);
        else {
          this.drawUnit(g, it.v);
          if (!it.v.ghost) bars.push(it.v);
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
      const cy = cy0 + v.oy;
      const tc = S.TEAMS[v.team] || S.TEAMS.P;
      const u = this.unit;
      g.save();
      g.globalAlpha = v.alpha * (v.ghost ? 0.55 : 1);
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
      const lift = v.hop + (v.type === 'wisp' ? 0 : 0);
      g.translate(cx, cy - lift);
      const sc = u * (v.scale || 1);
      g.scale(flip ? -sc : sc, sc);
      if (v.para > 0) g.filter = 'saturate(0.4) brightness(1.15)';
      S.drawUnit(g, v.type, v.team, view, this.time + v.phase, null);
      g.filter = 'none';
      g.restore();
    }

    drawBar(g, v) {
      if (v.alpha < 0.2 || v.type === 'shrub') {
        if (v.type === 'shrub' && v.alpha > 0.2) this.drawThinBar(g, v);
        return;
      }
      const [cx0, cy0] = this.center(v.x, v.y);
      const cx = cx0 + v.ox;
      const top = cy0 + v.oy - v.hop - (S.HEIGHT[v.type] || 40) * this.unit * (v.scale || 1);
      const bw = Math.max(18, this.tw * (v.boss ? 0.8 : v.vip ? 0.62 : 0.52));
      const bh = Math.max(3, this.tw * 0.075);
      const x = cx - bw / 2;
      const y = top - bh - 3;
      const frac = Math.max(0, Math.min(1, v.hp / v.maxHp));
      g.save();
      g.globalAlpha = v.alpha;
      g.fillStyle = 'rgba(12,10,16,0.85)';
      g.fillRect(x - 1, y - 1, bw + 2, bh + 2);
      g.fillStyle = v.poison ? '#9bd94a' : frac > 0.5 ? '#5fcf68' : frac > 0.25 ? '#e3b23c' : '#e0533d';
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
      if (v.rank > 1) {
        const s = Math.max(3, this.tw * 0.07);
        for (let i = 0; i < v.rank; i++) this.star(g, x + bw + s * 1.4 + i * s * 1.9, iy, s);
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
      const arc = kind === 'arrow' ? dist * 0.35 : kind === 'fire' || kind === 'orb' ? dist * 0.45 : dist * 0.08;
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
          const col = kind === 'fire' ? ['255,150,40', '#ffd27a'] : kind === 'orb' ? ['255,120,220', '#ffd2f2'] : ['170,110,255', '#e0c8ff'];
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
      switch (ev.kind) {
        case 'strike': {
          const ranged = Math.abs(tgt.x - ev.x) + Math.abs(tgt.y - ev.y) > 1;
          if (ranged) {
            this.sfx(type === 'archer' ? 'bow' : 'throw');
            await this.projectile(from, [tgt.x, tgt.y], type === 'archer' ? 'arrow' : 'knife', fast ? 120 : 260 + 25 * (Math.abs(tgt.x - ev.x) + Math.abs(tgt.y - ev.y)));
            await this.applyImpacts(group, state);
          } else {
            this.sfx('swing');
            const back = await lunge(tgt.x, tgt.y);
            this.slash(tgt.x, tgt.y);
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
          const charm = ev.dmg === 'magic' && type === 'enchantress';
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
        case 'nova': {
          const poison = type === 'wisp';
          this.sfx(poison ? 'poison' : 'zap');
          const r = Math.max(...tiles.map(([x, y]) => Math.abs(x - ev.x) + Math.abs(y - ev.y)), 1);
          this.ring(ev.x, ev.y, poison ? 'rgba(150,230,80,0.9)' : 'rgba(255,225,90,0.95)', r + 0.3, 420);
          if (poison) {
            for (const [x, y] of tiles) if (Math.random() < 0.6) this.particles(x, y, 3, ['#9bd94a', '#5fa82a'], { lift: 4, rise: 0.4, speed: 0.3, max: 0.8 });
          } else {
            const targets = group.filter((e) => e.t === 'dmg').map((e) => state.byId[e.uid]).filter(Boolean);
            for (const t of targets) this.bolt([from, [t.x, t.y]], 'rgba(255,220,80,A)', 300, 0.9);
          }
          await this.wait(fast ? 40 : 200);
          await this.applyImpacts(group, state);
          break;
        }
        case 'pray': {
          this.sfx('heal');
          if (v) {
            const [cx, cy] = this.center(v.x, v.y);
            this.effect(0.6, (g, k) => {
              g.save();
              g.globalAlpha = Math.sin(k * Math.PI) * 0.7;
              const gr = g.createLinearGradient(cx, cy, cx, cy - this.tw * 1.6);
              gr.addColorStop(0, 'rgba(255,230,140,0.8)');
              gr.addColorStop(1, 'rgba(255,230,140,0)');
              g.fillStyle = gr;
              g.fillRect(cx - this.tw * 0.18, cy - this.tw * 1.6, this.tw * 0.36, this.tw * 1.6);
              g.restore();
            });
          }
          this.ring(ev.x, ev.y, 'rgba(255,230,140,0.9)', 2.5, 500);
          await this.wait(fast ? 40 : 260);
          await this.applyImpacts(group, state);
          break;
        }
        case 'grow': {
          this.sfx('grow');
          this.particles(tgt.x, tgt.y, 10, ['#5aa046', '#8fd06a', '#3d7f33'], { lift: 4, rise: 0.5, max: 0.6 });
          await this.wait(fast ? 20 : 120);
          await this.applyImpacts(group, state);
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
            const col = e.dmgType === 'magic' ? '#d7b4ff' : e.dmgType === 'poison' ? '#b6f070' : e.dmgType === 'true' ? '#ffb0a0' : '#ffffff';
            this.addText(v.x, v.y, String(e.amount), col, { height: h, big: e.amount >= 25 });
            if (e.cat === 'back' && e.dmgType === 'phys') {
              const src = state && state.byId[e.src];
              const stab = src && src.traits.has('backstab');
              this.addText(v.x, v.y, stab ? 'BACKSTAB' : 'FROM BEHIND', '#ffcf6a', { height: h, dy: -this.tw * 0.28, max: 0.9 });
            }
            this.sfx(e.dmgType === 'poison' ? 'poison' : e.dmgType === 'magic' ? 'magichit' : 'hit');
            if (e.dmgType === 'poison') this.particles(v.x, v.y, 5, ['#9bd94a', '#5fa82a'], { lift: 14, rise: 0.4, speed: 0.3, max: 0.6 });
            break;
          }
          case 'block':
            if (!v) break;
            any = true;
            this.addText(v.x, v.y, 'BLOCK', '#a9d1ff', { height: h });
            this.sfx('block');
            this.particles(v.x, v.y, 6, ['#ffffff', '#cfe3ff'], { lift: 18, speed: 0.6, max: 0.35 });
            break;
          case 'heal':
            if (!v) break;
            any = true;
            v.hp = Math.min(v.maxHp, v.hp + e.amount);
            this.addText(v.x, v.y, '+' + e.amount, '#8ef08e', { height: h, dy: e.why === 'drain' ? this.tw * 0.15 : 0 });
            if (e.why !== 'drain') this.particles(v.x, v.y, 6, ['#b7ffb0', '#6fdc6f', '#fff3b0'], { lift: 10, rise: 0.8, speed: 0.25, max: 0.8 });
            break;
          case 'healblock':
            if (v) this.addText(v.x, v.y, 'NO HEAL', '#b6f070', { height: h, max: 0.9 });
            break;
          case 'status':
            if (!v) break;
            if (e.status === 'para') {
              v.para = e.turns;
              this.addText(v.x, v.y, 'PARALYZED', '#ffd84a', { height: h, dy: -this.tw * 0.25 });
            } else if (e.status === 'poison') {
              v.poison = true;
              this.addText(v.x, v.y, 'POISONED', '#b6f070', { height: h, dy: -this.tw * 0.25 });
            }
            break;
          case 'resist':
            if (v) this.addText(v.x, v.y, 'IMMUNE', '#e8e2d0', { height: h, dy: -this.tw * 0.25 });
            break;
          case 'cleanse':
          case 'cure':
            if (v) {
              v.para = 0;
              v.poison = false;
              if (e.t === 'cleanse') this.addText(v.x, v.y, 'CURED', '#fff3b0', { height: h, dy: -this.tw * 0.25 });
            }
            break;
          case 'death':
            if (!v) break;
            any = true;
            v.dying = true;
            this.sfx('death');
            this.particles(v.x, v.y, 12, ['#b9b2a8', '#7f786f', '#e8e2d8'], { lift: 12, rise: 0.4, speed: 0.6, max: 0.7 });
            this.tween(450, (k) => {
              v.alpha = 1 - k;
              v.oy = k * this.tw * 0.08;
            }).then(() => {
              if (v.dying) this.vis.delete(e.uid);
            });
            break;
          case 'revive':
            if (v) {
              v.dying = false;
              v.alpha = 1;
              v.oy = 0;
              v.hp = e.hp;
              this.addText(v.x, v.y, 'REBORN', '#ffcf6a', { height: h, big: true });
              this.particles(v.x, v.y, 16, ['#ffcf6a', '#ff8a2a', '#fff'], { lift: 10, rise: 1, max: 0.9 });
            }
            break;
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
          case 'summon': {
            const u = state && state.byId[e.uid];
            if (u) {
              const nv = this.makeVis(u);
              nv.scale = 0.2;
              this.vis.set(u.uid, nv);
              this.tween(260, (k) => (nv.scale = 0.2 + 0.8 * ease(k)));
            }
            break;
          }
          case 'wither':
            if (v) {
              v.dying = true;
              this.tween(300, (k) => (v.alpha = 1 - k)).then(() => this.vis.delete(e.uid));
            }
            break;
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

  AG.Render = { Board, PALETTES, portrait };
})(typeof window !== 'undefined' ? window : globalThis);
