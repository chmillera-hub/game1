// Stage: shots, camera, environments, actors and overlays -> one frame.
'use strict';
const fs = require('fs');
const path = require('path');
const { createCanvas } = require('@napi-rs/canvas');
const { clamp, smooth, easeInOut, fbm1, rgba, lerp } = require('./core');
const { drawCharacter, drawGlowOnly, headWorld } = require('./rig');
const { makeCast } = require('./chars');
const { Actor, LipSync, Track } = require('./acting');
const { buildSubs, drawSubs, drawLabel, drawTitle } = require('./text');

const ENV_LOADERS = {
  kitchen: () => require('./bg/kitchen'),
  porch: () => require('./bg/porch'),
  hearth: () => require('./bg/hearth'),
  nanaKitchen: () => require('./bg/nana').kitchen,
  memory: () => require('./bg/nana').memory,
  hospital: () => require('./bg/nana').hospital,
};
const DEFAULT_LIGHT = { keyDir: -2.3, keyColor: '#ffe2bc', keyAmt: 0.7, rimDir: -0.5, rimColor: '#ffd9a8', rimAmt: 0.35, shadowColor: '#35233d', shadowAmt: 0.32, ambient: '#fff0dc', ambientAmt: 0.08 };
const envCache = {};
function env(name) {
  if (envCache[name] !== undefined) return envCache[name];
  try { envCache[name] = ENV_LOADERS[name](); } catch (e) {
    console.error(`[stage] env ${name} unavailable: ${e.message.split('\n')[0]}`);
    envCache[name] = {
      ENV: { extents: { x0: -2000, y0: -2000, x1: 4000, y1: 4000 }, anchors: {} },
      drawBack: (ctx) => { const g = ctx.createLinearGradient(0, -500, 0, 2400); g.addColorStop(0, '#6d5c52'); g.addColorStop(1, '#2f2622'); ctx.fillStyle = g; ctx.fillRect(-2000, -2000, 6000, 6000); },
      drawFront: () => {}, lightAt: () => DEFAULT_LIGHT,
    };
  }
  return envCache[name];
}

class Stage {
  constructor(schedule) {
    this.sched = schedule;
    this.lines = Object.fromEntries(schedule.lines.map((l) => [l.id, l]));
    this.cast = makeCast();
    this.actors = {};
    this.shots = [];
    this.labels = [];
    this.titles = [];
    this.subsOn = true;
    this.duration = schedule.duration;
    this.cues = { scenes: [], sfx: [], amb: [] };
  }
  // ---- time helpers
  L(id) { const l = this.lines[id]; if (!l) throw new Error('no line ' + id); return l; }
  t0(id) { return this.L(id).t0; }
  t1(id) { return this.L(id).t1; }
  W(id, word, k = 0) {
    const l = this.L(id);
    const norm = (s) => s.toLowerCase().replace(/[^a-z0-9']/g, '');
    let n = 0;
    for (const w of l.words) if (norm(w.w) === norm(word)) { if (n === k) return w.t0; n++; }
    if (typeof word === 'number') return l.words[word].t0;
    throw new Error(`no word ${word} in ${id}`);
  }
  WE(id, word, k = 0) { const t = this.W(id, word, k); return this.L(id).words.find((w) => w.t0 === t).t1; }
  // ---- actors
  actor(id, rig, base, opts) {
    const a = new Actor(id, { x: 0, y: 0, s: 1, pose: 'stand', facing: 0, lean: 0, head: { yaw: 0, pitch: 0, tilt: 0 }, gaze: [0, 0], arms: {}, glow: 1, flame: 0, ...base }, opts);
    a.rig = rig;
    this.actors[id] = a;
    return a;
  }
  // assign speech lines (by predicate) to an actor for lip-sync
  speak(actorId, pred, gain = 1) {
    const lines = this.sched.lines.filter(pred);
    this.actors[actorId].lip = new LipSync(lines, gain);
  }
  // listeners nod on every third stressed syllable of other speakers' lines
  listen(actorId, pred) {
    const times = [];
    let k = 0;
    for (const l of this.sched.lines.filter(pred)) for (const p of l.phones) if (p[0] === 'ˈ') { if (k++ % 3 === 1) times.push(p[1]); }
    this.actors[actorId].listenStress = times;
  }
  shot(s) { this.shots.push(s); this.shots.sort((a, b) => a.t0 - b.t0); return s; }
  label(t, actorId, o = {}) { this.labels.push({ t, actorId, ...o }); }
  title(t0, t1, lines, y, o = {}) { this.titles.push({ t0, t1, lines, y, ...o }); }
  sfx(t, name, gain = 1, pan = 0) { this.cues.sfx.push({ t: +t.toFixed(3), name, gain, pan }); }
  amb(name, t0, t1, gain = 1) { this.cues.amb.push({ name, t0: +t0.toFixed(3), t1: +t1.toFixed(3), gain }); }
  scene(name, t0, t1, mood) { this.cues.scenes.push({ name, t0: +t0.toFixed(3), t1: +t1.toFixed(3), mood }); }

  shotAt(T) {
    let cur = null, idx = -1;
    for (let i = 0; i < this.shots.length; i++) if (this.shots[i].t0 <= T) { cur = this.shots[i]; idx = i; }
    return [cur, idx];
  }
  camAt(shot, T) {
    if (!shot._cam) {
      const tr = new Track(shot.cam[0].slice(1, 4));
      for (const k of shot.cam) tr.add(k[0], k.slice(1, 4), k[4] ?? 0.001, k[5] || easeInOut);
      shot._cam = tr;
    }
    const [x, y, z] = shot._cam.at(T);
    const hh = shot.handheld ?? 1;
    return { x: x + fbm1(T * 0.35, 3) * 3 * hh, y: y + fbm1(T * 0.31, 7) * 3 * hh, z };
  }

  // ---- drawing
  drawShot(ctx, shot, T, W, H) {
    const cam = this.camAt(shot, T);
    const E = env(shot.env);
    const eo = typeof shot.envOpt === 'function' ? shot.envOpt(T) : (shot.envOpt || {});
    ctx.save();
    ctx.setTransform(W / 1080, 0, 0, H / 1920, 0, 0);
    ctx.translate(540, 960);
    ctx.scale(cam.z, cam.z);
    ctx.translate(-cam.x, -cam.y);
    E.drawBack(ctx, T, eo);
    if (shot.under) shot.under(ctx, T, this, eo);
    const ids = typeof shot.actors === 'function' ? shot.actors(T) : (shot.actors || []);
    const states = {};
    for (const id of ids) states[id] = this.actors[id].sample(T);
    if (shot.fixGaze) shot.fixGaze(states, T);
    // glows first, so no character's aura washes over another character
    for (const id of [...ids, ...(shot.foreground || [])]) {
      const S = states[id] || this.actors[id].sample(T);
      if (!S.hidden) drawGlowOnly(ctx, this.cast[this.actors[id].rig], S, T);
      S.glowDone = true;
      states[id] = S;
    }
    for (const id of ids) {
      const a = this.actors[id], S = states[id];
      if (S.hidden) continue;
      const C = this.cast[a.rig];
      const Lt = { ...DEFAULT_LIGHT, ...(E.lightAt ? E.lightAt(S.x, S.y - 300 * (S.s || 1), T, eo) : {}) };
      if (shot.light) Object.assign(Lt, typeof shot.light === 'function' ? shot.light(T, id) : shot.light);
      if (this.lightMod) this.lightMod(shot.env, T, id, S, Lt, eo);
      if (shot.beforeActor) shot.beforeActor(ctx, T, id, S, this);
      S._light = Lt;
      if (shot.armsFront && shot.armsFront.includes(id)) S.layer = 'noFrontArms';
      drawCharacter(ctx, C, S, Lt, T);
      if (shot.afterActor) shot.afterActor(ctx, T, id, S, this);
    }
    if (shot.over) shot.over(ctx, T, this, eo);
    E.drawFront(ctx, T, eo);
    for (const id of shot.foreground || []) {
      const a = this.actors[id], S = states[id];
      states[id] = S;
      if (S.hidden) continue;
      const Lt = { ...DEFAULT_LIGHT, ...(E.lightAt ? E.lightAt(S.x, S.y - 300 * (S.s || 1), T, eo) : {}) };
      if (shot.light) Object.assign(Lt, typeof shot.light === 'function' ? shot.light(T, id) : shot.light);
      if (this.lightMod) this.lightMod(shot.env, T, id, S, Lt, eo);
      drawCharacter(ctx, this.cast[a.rig], S, Lt, T);
    }
    if (shot.front) shot.front(ctx, T, this, eo, states);
    for (const id of shot.armsFront || []) {
      const S = states[id];
      if (!S || S.hidden) continue;
      drawCharacter(ctx, this.cast[this.actors[id].rig], { ...S, layer: 'armsOnly' }, S._light, T);
    }
    if (shot.top) shot.top(ctx, T, this, eo, states);
    ctx.restore();
    // grade + vignette in screen space
    ctx.save();
    ctx.setTransform(W / 1080, 0, 0, H / 1920, 0, 0);
    const gr = typeof shot.grade === 'function' ? shot.grade(T) : shot.grade;
    if (gr) {
      ctx.globalCompositeOperation = gr.mode || 'soft-light';
      ctx.fillStyle = rgba(gr.color, gr.alpha ?? 0.3);
      ctx.fillRect(0, 0, 1080, 1920);
      ctx.globalCompositeOperation = 'source-over';
    }
    const vg = shot.vignette ?? 0.35;
    if (vg > 0) {
      const g = ctx.createRadialGradient(540, 900, 500, 540, 900, 1250);
      g.addColorStop(0, 'rgba(10,6,12,0)'); g.addColorStop(1, `rgba(10,6,12,${vg})`);
      ctx.fillStyle = g; ctx.fillRect(0, 0, 1080, 1920);
    }
    if (shot.screen) shot.screen(ctx, T, this);
    ctx.restore();
    return { cam, states };
  }

  render(ctx, T, W, H) {
    const [shot, idx] = this.shotAt(T);
    if (!shot) return;
    const tr = shot.trans;
    let info = this.drawShot(ctx, shot, T, W, H);
    if (tr && idx > 0 && T < shot.t0 + tr.dur) {
      const p = smooth((T - shot.t0) / tr.dur);
      if (tr.type === 'dissolve') {
        if (!this._off || this._off.width !== W) this._off = createCanvas(W, H);
        const o = this._off.getContext('2d');
        o.setTransform(1, 0, 0, 1, 0, 0);
        o.clearRect(0, 0, W, H);
        this.drawShot(o, this.shots[idx - 1], T, W, H);
        ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1 - p; ctx.drawImage(this._off, 0, 0); ctx.restore();
      } else if (tr.type === 'flash') {
        ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.fillStyle = rgba(tr.color || '#fff4dc', (1 - p) * (tr.amt ?? 1)); ctx.fillRect(0, 0, W, H); ctx.restore();
      }
    }
    // flash-out at the end of a shot
    const next = this.shots[idx + 1];
    if (next && next.trans && next.trans.type === 'flash' && next.trans.pre) {
      const p = smooth((T - (next.t0 - next.trans.pre)) / next.trans.pre);
      if (p > 0) { ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = rgba(next.trans.color || '#fff4dc', p * (next.trans.amt ?? 1)); ctx.fillRect(0, 0, W, H); ctx.restore(); }
    }
    // overlays: labels, titles, subtitles
    ctx.save();
    ctx.setTransform(W / 1080, 0, 0, H / 1920, 0, 0);
    for (const lb of this.labels) {
      const age = T - lb.t;
      if (age < 0 || age > (lb.dur || 3.2)) continue;
      const S = info.states[lb.actorId];
      if (!S) continue;
      const a = this.actors[lb.actorId], C = this.cast[a.rig];
      const [hx, hy, hh] = headWorld(C, S);
      const extra = lb.dy || 0;
      const sx = 540 + (hx - info.cam.x) * info.cam.z, sy = 960 + (hy - hh * 0.62 + extra - info.cam.y) * info.cam.z;
      drawLabel(ctx, lb.text || C.label, lb.emoji ?? C.emoji, lb.color || C.color, sx, sy, age, lb.dur || 3.2, lb.side || 0);
    }
    for (const ti of this.titles) {
      if (T < ti.t0 || T > ti.t1) continue;
      const a = (ti.fadeIn === 0 ? 1 : smooth((T - ti.t0) / (ti.fadeIn ?? 0.6))) * (1 - smooth((T - ti.t1 + (ti.fadeOut ?? 0.6)) / (ti.fadeOut ?? 0.6)));
      drawTitle(ctx, ti.lines, ti.y, a);
    }
    if (this.subsOn) {
      if (!this._subs) this._subs = buildSubs(this.sched, ctx);
      drawSubs(ctx, this._subs, T, shot.subY || 1520);
    }
    ctx.restore();
  }
}

module.exports = { Stage, env };
