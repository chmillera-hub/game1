// The director's toolkit: puppets, camera, lights and props on one timeline.

const { Track, Steps, clamp, lerp } = require('./core');
const { Puppet, EXPR, POSES } = require('./puppet');

class Stage {
  constructor(tl) {
    this.tl = tl;
    this.duration = tl.duration;
    this.puppets = {
      marcus: new Puppet('marcus', 270, 1),
      priya: new Puppet('priya', 540, 2),
      theo: new Puppet('theo', 810, 3),
    };
    this.cam = new Steps({ who: 'wide' });
    this.L = {
      tv: new Track(1), lamp: new Track(1), morning: new Track(0), rain: new Track(1), tvFlash: new Track(0),
    };
    this.itemsS = new Steps(['snacks']);
    this.orderS = new Steps(['marcus', 'priya', 'theo']);
    this.lineById = {};
    for (const ln of tl.lines) {
      this.lineById[ln.id] = ln;
      if (this.puppets[ln.speaker]) this.puppets[ln.speaker].lines.push(ln);
    }
    for (const v of tl.vocals || []) {
      this.lineById[v.id] = v;
      if (this.puppets[v.speaker]) this.puppets[v.speaker].vocals.push(v);
    }
  }

  // ---- timeline lookups
  S(id) { const l = this.lineById[id]; if (!l) throw new Error('no line ' + id); return l.start; }
  E(id) { const l = this.lineById[id]; if (!l) throw new Error('no line ' + id); return l.end; }
  M(name) { if (!(name in this.tl.marks)) throw new Error('no mark ' + name); return this.tl.marks[name]; }

  // ---- acting
  each(who, fn) { (Array.isArray(who) ? who : [who]).forEach((w) => fn(this.puppets[w])); }

  expr(who, t, name, dur = 0.45, extra = {}) {
    const e = EXPR[name];
    if (!e) throw new Error('no expr ' + name);
    this.each(who, (p) => {
      for (const [k, v] of Object.entries({ ...e, ...extra })) p.T[k].set(t, v, dur);
    });
  }

  set(who, t, obj, dur = 0.4, e = 'inOut') {
    this.each(who, (p) => { for (const [k, v] of Object.entries(obj)) p.T[k].set(t, v, dur, e); });
  }

  look(who, t, target, opts = {}) {
    this.each(who, (p) => p.gaze.set(t, { target, dur: opts.dur || 0.22, head: opts.head, ox: opts.ox || 0, oy: opts.oy || 0, blink: opts.blink }));
  }

  blink(who, t) { this.each(who, (p) => p.forcedBlinks.push(t)); }
  hold(who, t0, t1) { this.each(who, (p) => p.noBlink.push([t0, t1])); } // no auto-blinks (a stare)

  nod(who, t, n = 1, amp = 0.2, period = 0.42) {
    this.each(who, (p) => {
      for (let i = 0; i < n; i++) {
        p.T.nodP.set(t + i * period, amp, period * 0.45);
        p.T.nodP.set(t + i * period + period * 0.45, 0, period * 0.55);
      }
    });
  }

  shake(who, t, n = 2, amp = 0.14, period = 0.34) {
    this.each(who, (p) => {
      for (let i = 0; i < n; i++) {
        p.T.shakeT.set(t + i * period, (i % 2 ? -1 : 1) * amp, period * 0.9);
      }
      p.T.shakeT.set(t + n * period, 0, period);
    });
  }

  pose(who, t, name, dur = 0.55, e = 'inOut') {
    const ps = POSES[name];
    if (!ps) throw new Error('no pose ' + name);
    this.each(who, (p) => {
      p.T.lx.set(t, ps.l[0], dur, e); p.T.ly.set(t, ps.l[1], dur, e);
      p.T.rx.set(t, ps.r[0], dur, e); p.T.ry.set(t, ps.r[1], dur, e);
      const lh = ps.lh || [-0.6, 1], rh = ps.rh || [0.6, 1];
      p.T.lhx.set(t, lh[0], dur, e); p.T.lhy.set(t, lh[1], dur, e);
      p.T.rhx.set(t, rh[0], dur, e); p.T.rhy.set(t, rh[1], dur, e);
      const fs = ps.fs || [0, 0];
      p.T.lfs.set(t, fs[0], dur, e); p.T.rfs.set(t, fs[1], dur, e);
      const shape = ps.shape || 'open';
      p.shapeL.set(t + dur * 0.5, shape); p.shapeR.set(t + dur * 0.5, shape);
      const fr = ps.front || '';
      p.frontL.set(t + dur * (fr.includes('l') ? 0.5 : 0.35), fr.includes('l'));
      p.frontR.set(t + dur * (fr.includes('r') ? 0.5 : 0.35), fr.includes('r'));
      p.propS.set(t + dur * 0.5, ps.prop || null);
      if (ps.propAt) { p.T.propX.set(t, ps.propAt[0], dur, e); p.T.propY.set(t, ps.propAt[1], dur, e); }
    });
  }

  move(who, t, x, dur = 0.8, e = 'inOut') { this.each(who, (p) => p.T.x.set(t, x, dur, e)); }
  show(who, t, v) { this.each(who, (p) => p.visible.set(t, v)); }

  // ---- camera / world
  shot(t, spec) { this.cam.set(t, spec); }
  light(t, obj, dur = 0.5, e = 'inOut') { for (const [k, v] of Object.entries(obj)) this.L[k].set(t, v, dur, e); }
  items(t, list) { this.itemsS.set(t, list); }
  order(t, list) { this.orderS.set(t, list); }

  finalize() { for (const p of Object.values(this.puppets)) p.finalize(this.duration + 2); }

  lightAt(t) {
    const o = {};
    for (const [k, tr] of Object.entries(this.L)) o[k] = tr.at(t);
    return o;
  }

  camera(t) {
    const { cur } = this.cam.keyAt(t);
    const s = cur.v, t0 = cur.t;
    let cx = 540, cy = 960, z = s.z || 1;
    const who = s.who;
    if (who && who !== 'wide') {
      const list = Array.isArray(who) ? who : [who];
      const heads = list.map((w) => this.puppets[w].head(t));
      const xs = heads.map((h) => h[0]), ys = heads.map((h) => h[1]);
      const span = Math.max(...xs) - Math.min(...xs);
      z = s.z || (list.length > 1 ? clamp(1080 / (span + 470), 1, 2.6) : 2.6);
      cx = xs.reduce((a, b) => a + b, 0) / xs.length;
      cy = ys.reduce((a, b) => a + b, 0) / ys.length + 230 / z;
    } else if (s.cy) {
      cy = s.cy;
    }
    const dt = Math.max(0, t - t0);
    z *= 1 + (s.dz || 0) * dt;
    cx += (s.dx || 0) + (s.px || 0) * dt;
    cy += (s.dy || 0) + (s.py || 0) * dt;
    return { cx, cy, z };
  }
}

module.exports = { Stage };
