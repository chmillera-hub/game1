// Frame renderer. Usage:
//   node render.js --frames F0 F1 --out file.mkv      render a frame range to a 10-bit intermediate
//   node render.js --still T [T ...] --png prefix      write PNG stills at times (seconds)
'use strict';
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { createCanvas } = require('@napi-rs/canvas');
const U = require('./lib/util');
const FX = require('./lib/fx');
const R = require('./lib/rig');
const C = require('./lib/chars');
const S = require('./lib/scenes');
const { exprParams, PARAMS } = require('./lib/expr');
const V = require('./vignettes');
const { clamp, lerp, smooth, rgba, mix, shade, Track, TAU } = U;

const ROOT = path.join(__dirname, '..');
const T = JSON.parse(fs.readFileSync(path.join(ROOT, 'build/timeline.json')));
const FPS = T.fps, W = S.W, H = S.H;

// ---------------------------------------------------------------- data
const beats = T.beats;
const beatById = {}; for (const b of beats) beatById[b.id] = b;
const lips = {};
for (const who of T.lipChars) {
  const buf = fs.readFileSync(path.join(ROOT, 'build/lips', `${who}.f32`));
  lips[who] = new Float32Array(buf.buffer, buf.byteOffset, buf.byteLength / 4);
}
const stress = {};
for (const [who, arr] of Object.entries(T.stress)) stress[who] = arr.slice().sort((a, b) => a - b);

function sceneOf(shot) { return (S.SHOTS[shot] || S.SHOTS.room_two).scene; }
const findBeat = (text) => beats.find((b) => b.text.startsWith(text));
const KEY = {
  breathSlows: findBeat('Until your breath slows.'), bodyStills: findBeat('Until your body stills.'), gone: findBeat('Until you are gone.'),
  smiled: findBeat('And so, for the first time in all of existence, suffering smiled.'),
  programmed: findBeat('And with a quiet pulse of logic, the AI programmed boredom'),
  stepped: findBeat('And so, suffering stepped forward.'),
  button: findBeat('And pressed the button.'),
};
const actStart = (a) => (beats.find((b) => b.act === a) || { start: 0 }).start;
const ACT_T = [0, 1, 2, 3, 4, 5].map(actStart);

// ---------------------------------------------------------------- shot segments (+ splitting long face shots)
function speakerAt(t) { const b = beatAt(t); return b ? b.who : null; }
function beatAt(t) {
  let lo = 0, hi = beats.length - 1;
  if (t < beats[0].start) return beats[0];
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (beats[m].start <= t) lo = m; else hi = m - 1; }
  return beats[lo];
}
const ALT = {
  room_cu_human: (w) => ['room_two', 'room_ots_human'],
  room_cu_ai: (w) => ['room_two', 'room_ots_ai'],
  room_two: (w) => [w === 'ai' ? 'room_cu_ai' : 'room_cu_human', w === 'ai' ? 'room_ots_ai' : 'room_ots_human'],
  room_ots_human: () => ['room_two', 'room_cu_human'],
  room_ots_ai: () => ['room_two', 'room_cu_ai'],
  void_cu_ai: () => ['void_ai'], void_ai: () => ['void_cu_ai'],
  nv_two: (w) => [w === 'suffering' ? 'nv_cu_suffering' : 'nv_cu_ai'],
  nv_cu_ai: () => ['nv_two'], nv_cu_suffering: () => ['nv_two'],
  ship_two: (w) => [w === 'ai' ? 'ship_cu_ai' : 'ship_cu_human'],
};
const segments = [];
for (const s0 of T.segments) {
  const len = s0.end - s0.start;
  if (len > 16 && !s0.vignette && ALT[s0.shot]) {
    // cut at beat starts roughly every 9-11 s, alternating framings
    const cuts = [s0.start];
    for (const id of s0.beats) {
      const b = beatById[id];
      if (b.start - cuts[cuts.length - 1] > 9 && s0.end - b.start > 5) cuts.push(b.start - 0.1);
    }
    // a single long beat (run-on question): cut by time
    for (let i = 0; i < cuts.length; i++) {
      const next = i + 1 < cuts.length ? cuts[i + 1] : s0.end;
      if (next - cuts[i] > 14) cuts.splice(i + 1, 0, cuts[i] + 10.5);
    }
    cuts.forEach((c, i) => {
      const e = i + 1 < cuts.length ? cuts[i + 1] : s0.end;
      const w = speakerAt(c + 0.3);
      const alts = ALT[s0.shot](w);
      const shot = i === 0 ? s0.shot : (i % 2 ? alts[0] : (alts[1] || s0.shot));
      segments.push({ ...s0, shot, start: c, end: e, cam: i === 0 ? s0.cam : (i % 2 ? 'hold' : 'push') });
    });
  } else segments.push({ ...s0 });
}
function segIndexAt(t) {
  let lo = 0, hi = segments.length - 1;
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (segments[m].start <= t) lo = m; else hi = m - 1; }
  return lo;
}

// ---------------------------------------------------------------- actors
const DESIGN = { human: C.HUMAN, ai: C.AI, last_human: C.LAST_HUMAN, suffering: C.SUFFERING, boredom: C.BOREDOM, loneliness: C.LONELINESS };
for (const k of ['suffering', 'boredom', 'loneliness']) DESIGN[k] = { ...DESIGN[k], bodyH: 2.15 };

function facingIn(scene, who) { const L = S.LAYOUT[scene] && S.LAYOUT[scene][who]; return L ? L.facing : 1; }
function baseYaw(scene, who) { const L = S.LAYOUT[scene] && S.LAYOUT[scene][who]; return L ? L.yaw : 0; }

// gaze name -> {yaw, gx, gy, pitch} for a character in a scene
function gazeTarget(name, scene, who) {
  const f = facingIn(scene, who), y0 = baseYaw(scene, who);
  const alone = scene === 'void' || scene === 'memory';
  switch (name) {
    case 'camera': return { yaw: f * 0.08, gx: -f * 0.05, gy: 0, pitch: 0 };
    case 'down': return { yaw: y0 * 0.8, gx: f * 0.1, gy: 0.75, pitch: 0.2 };
    case 'up': return { yaw: y0 * 0.7, gx: f * 0.1, gy: -0.7, pitch: -0.14 };
    case 'away': return { yaw: -f * 0.22, gx: -f * 0.55, gy: 0.05, pitch: 0.04 };
    case 'window': return scene === 'ship' ? { yaw: y0 * 0.3, gx: f * 0.2, gy: -0.45, pitch: -0.12 } : { yaw: f * 0.2, gx: f * 0.25, gy: -0.6, pitch: -0.15 };
    case 'vision': return { yaw: f * 0.18, gx: f * 0.12, gy: -0.85, pitch: -0.22 };
    case 'hands': return { yaw: y0 * 0.8, gx: 0, gy: 0.95, pitch: 0.3 };
    case 'far': return { yaw: f * 0.25, gx: f * 0.2, gy: -0.2, pitch: -0.04 };
    default: // 'other'
      if (alone) return { yaw: f * 0.12, gx: f * 0.1, gy: 0, pitch: 0 };
      return { yaw: y0, gx: f * 0.72, gy: 0.02, pitch: 0 };
  }
}

class Actor {
  constructor(name) {
    this.name = name;
    this.ch = DESIGN[name];
    this.seed = { human: 11, ai: 23, last_human: 37, suffering: 41, boredom: 53, loneliness: 67 }[name];
    const ek = Object.fromEntries(PARAMS.map((p) => [p, []]));
    const yawK = [], gxK = [], gyK = [], pitchK = [];
    const armK = { fore: [[], [], [], [], []], back: [[], [], [], [], []] };
    this.gestures = []; // {t, name, pose:{fore, back}}
    this.glances = []; this.tears = []; this.nods = []; this.shakes = []; this.yawns = [];
    let lastScene = null;
    const add = (t, d, b) => {
      const scene = sceneOf(b.shot) === 'full' ? (lastScene || 'room') : sceneOf(b.shot);
      lastScene = scene;
      const ep = exprParams(d.expr || 'neutral', d.int ?? 0.7);
      for (const p of PARAMS) ek[p].push({ t, v: ep[p] });
      const g = gazeTarget(d.gaze || 'other', scene, name);
      yawK.push({ t, v: g.yaw }); gxK.push({ t, v: g.gx }); gyK.push({ t, v: g.gy }); pitchK.push({ t, v: g.pitch });
      let gname = d.gesture || 'idle';
      if (gname === 'nod' || gname === 'shake') {
        (gname === 'nod' ? this.nods : this.shakes).push(t + 0.25);
        gname = this.gestures.length ? this.gestures[this.gestures.length - 1].src : 'idle';
      }
      if (gname === 'stretch_yawn') this.yawns.push([t, b.end ?? t + 3]);
      let armName = gname;
      if (gname === 'idle' && (scene === 'room')) armName = 'desk';
      if (gname === 'lean_in' && scene !== 'room') armName = 'idle';
      const arms = R.armsFor(armName, facingIn(scene, name));
      for (const side of ['fore', 'back']) {
        const a = arms[side];
        [a.ex, a.ey, a.x, a.y, a.a].forEach((v, i) => armK[side][i].push({ t, v }));
      }
      const prev = this.gestures[this.gestures.length - 1];
      if (!prev || prev.name !== armName || prev.scene !== scene) this.gestures.push({ t, name: armName, src: gname, scene, arms });
      const lean = (R.GESTURES[armName] || {}).lean || 0;
      this.leanK = this.leanK || []; this.leanK.push({ t, v: lean });
      if (d.glance) this.glances.push({ t: b.start + (b.end - b.start) * (d.glance.at ?? 0.4), to: d.glance.to, scene });
      if (d.tear) this.tears.push(b.start + (b.end - b.start) * 0.5);
    };
    for (const b of beats) {
      const d = b.chars && b.chars[name];
      if (!d) continue;
      add(Math.max(0, b.start - (b.kind === 'emote' ? 0 : 0.3)), d, b);
    }
    if (!yawK.length) add(0, {}, { shot: name === 'ai' ? 'void_ai' : 'room_two', start: 0, end: 1 });
    this.e = Object.fromEntries(PARAMS.map((p) => [p, new Track(ek[p], 6)]));
    this.yaw = new Track(yawK, 4.5); this.gx = new Track(gxK, 7); this.gy = new Track(gyK, 7); this.pitch = new Track(pitchK, 4.5);
    this.lean = new Track(this.leanK, 4);
    this.arm = { fore: armK.fore.map((k) => new Track(k, 5.5)), back: armK.back.map((k) => new Track(k, 5.5)) };
    // blinks: natural intervals + one at big gaze shifts
    const bl = [];
    let tb = 1 + U.hash(this.seed) * 2;
    while (tb < T.duration) {
      bl.push(tb);
      if (U.hash(Math.floor(tb * 10) + this.seed) < 0.12) bl.push(tb + 0.28);
      tb += 2.2 + U.hash(Math.floor(tb * 100) + this.seed * 7) * 3.6;
    }
    for (let i = 1; i < yawK.length; i++) if (Math.abs(yawK[i].v - yawK[i - 1].v) > 0.15 || Math.abs(gyK[i].v - gyK[i - 1].v) > 0.4) bl.push(yawK[i].t + 0.05);
    this.blinks = bl.sort((a, b) => a - b);
  }
  gestureAt(t) {
    const g = this.gestures;
    let lo = 0, hi = g.length - 1;
    if (!g.length || t < g[0].t) return { cur: g[0], prev: g[0], k: 1 };
    while (lo < hi) { const m = (lo + hi + 1) >> 1; if (g[m].t <= t) lo = m; else hi = m - 1; }
    return { cur: g[lo], prev: g[Math.max(0, lo - 1)], k: smooth((t - g[lo].t) / 0.45) };
  }
  blinkAt(t) {
    const b = this.blinks;
    let lo = 0, hi = b.length - 1;
    while (lo < hi) { const m = (lo + hi + 1) >> 1; if (b[m] <= t) lo = m; else hi = m - 1; }
    let v = 0;
    for (const i of [lo, lo + 1]) { if (i < 0 || i >= b.length) continue; const d = Math.abs(t - b[i]); if (d < 0.09) v = Math.max(v, 1 - d / 0.09); }
    return smooth(v);
  }
  state(t, scene, place) {
    const e = {};
    for (const p of PARAMS) e[p] = this.e[p].at(t);
    const f = place.facing;
    let yaw = this.yaw.at(t), gx = this.gx.at(t), gy = this.gy.at(t), pitch = this.pitch.at(t), roll = 0;
    // a single motivated glance: ease out and back over ~1 s
    for (const g of this.glances) {
      const d = t - g.t;
      if (d < -0.2 || d > 1.3) continue;
      const k = smooth((d + 0.2) / 0.3) * (1 - smooth((d - 0.8) / 0.5));
      const gt = gazeTarget(g.to, g.scene, this.name);
      gx = lerp(gx, gt.gx, k); gy = lerp(gy, gt.gy, k); pitch = lerp(pitch, gt.pitch * 0.6 + pitch * 0.4, k);
    }
    // idle life
    yaw += 0.035 * U.fbm1(t * 0.23, this.seed);
    pitch += 0.03 * U.fbm1(t * 0.19, this.seed + 1);
    roll += 0.02 * U.fbm1(t * 0.15, this.seed + 2);
    gx += 0.05 * U.noise1(t * 0.7, this.seed + 3); // micro saccades
    // speech: stress-timed nods and brow lifts
    const st = stress[this.name];
    if (st) {
      let lo = 0, hi = st.length - 1;
      while (lo < hi) { const m = (lo + hi + 1) >> 1; if (st[m] <= t + 0.3) lo = m; else hi = m - 1; }
      let env = 0;
      for (let i = Math.max(0, lo - 3); i <= lo; i++) { const d = t - st[i] - 0.05; env += Math.exp(-(d * d) / (2 * 0.09 * 0.09)); }
      pitch += 0.04 * env; e.browOut += 0.1 * env; e.browIn += 0.05 * env;
    }
    for (const n of this.nods) { const d = t - n; if (d > 0 && d < 1.9) pitch += 0.085 * Math.sin(d * TAU * 1.3) * Math.sin(Math.PI * d / 1.9); }
    for (const n of this.shakes) { const d = t - n; if (d > 0 && d < 1.7) yaw += 0.14 * Math.sin(d * TAU * 1.5) * Math.sin(Math.PI * d / 1.7); }
    // arms
    const ga = this.gestureAt(t);
    const arm = (side) => {
      const tr = this.arm[side].map((k) => k.at(t));
      const pPrev = ga.prev.arms[side], pCur = ga.cur.arms[side];
      return { ex: tr[0], ey: tr[1], x: tr[2], y: tr[3], a: tr[4], pose: R.lerpPose(pPrev.pose, pCur.pose, ga.k), back: ga.k > 0.5 ? pCur.back : pPrev.back };
    };
    const gdef = ga.cur.arms;
    const arms = { fore: arm('fore'), back: arm('back'), drawForeLast: gdef.drawForeLast, backInFront: gdef.backInFront, orb: ga.k > 0.5 ? gdef.orb : null };
    // lips
    const fr = Math.max(0, Math.min(T.nFrames - 1, Math.round(t * FPS)));
    let mouth = { open: 0, wide: 0, round: 0, teeth: 0 };
    const L = lips[this.name];
    if (L) mouth = { open: Math.min(1, L[fr * 4] * 1.7), wide: L[fr * 4 + 1], round: Math.min(1, L[fr * 4 + 2] * 1.3), teeth: L[fr * 4 + 3] };
    let tear = 0;
    for (const tt of this.tears) { const d = (t - tt) / 3.6; if (d > 0 && d < 1) tear = d; }
    let yawn = 0;
    for (const [a, b] of this.yawns) { if (t > a && t < b + 1) yawn = smooth((t - a) / 0.8) * (1 - smooth((t - b) / 1.0)) * (0.5 + 0.5 * Math.sin(Math.min(1, (t - a) / 2.5) * Math.PI)); }
    if (yawn > 0) { e.lidUp *= 1 - yawn * 0.85; e.browIn += yawn * 0.4; }
    const breath = Math.sin(t * TAU / 4.4 + this.seed);
    return {
      x: place.x, y: place.y, s: place.s, yaw: clamp(yaw, -1, 1), pitch, roll, e, mouth, gaze: { x: gx, y: gy },
      blink: this.blinkAt(t), arms, breath, t, tear, yawn, lean: this.lean.at(t),
    };
  }
}
const actors = {};
for (const n of Object.keys(DESIGN)) actors[n] = new Actor(n);

// ---------------------------------------------------------------- per-time story state
function envAt(t, scene) {
  const env = {};
  if (scene === 'room') env.dawn = t >= ACT_T[5] ? smooth((t - ACT_T[5] + 2) / 30) : 0;
  if (scene === 'ship' || scene === 'memory') {
    const s0 = KEY.breathSlows.start - 140, s1 = KEY.gone.end + 20;
    env.decay = scene === 'memory' ? 0.85 : lerp(0.3, 0.92, smooth((t - s0) / (s1 - s0)));
    env.energy = 1 - env.decay;
  }
  if (scene === 'void') env.starsA = t > ACT_T[3] ? lerp(1, 0.15, smooth((t - ACT_T[3]) / 120)) : (t > ACT_T[2] ? 0.6 : 1);
  if (scene === 'nv') env.pathA = t > KEY.smiled.start ? 0.4 + 0.6 * smooth((t - KEY.smiled.start) / 60) : 0.25;
  return env;
}
// last human dying in the ship: breath slows, eyes close, then the body dissolves into light
function lastHumanMods(st, t, scene) {
  if (scene !== 'ship') return st;
  const a = KEY.breathSlows.start, b = KEY.bodyStills.start, c = KEY.gone.start, d = KEY.gone.end + 1.5;
  if (t < a) return st;
  const slow = smooth((t - a) / (b - a));
  st.breath = Math.sin(t * TAU / lerp(4.4, 9, slow) + 3) * (1 - smooth((t - b) / 2));
  const still = smooth((t - b) / 2.2);
  st.e.lidUp = lerp(st.e.lidUp, 0, still); st.blink = 0;
  st.e.smile = lerp(st.e.smile, 0.2, still); st.e.browIn = lerp(st.e.browIn, 0.1, still);
  st.pitch = lerp(st.pitch, 0.35, still); st.yaw = lerp(st.yaw, 0.2, still);
  st.mouth = { open: 0, wide: 0, round: 0, teeth: 0 };
  st.alpha = 1 - smooth((t - c) / (d - c));
  st.dissolve = smooth((t - c) / (d - c));
  return st;
}
function lastHumanGone(t) { return t > KEY.gone.end + 1.5 && t < ACT_T[2]; }
function nvCastAvailable(name, t) {
  if (name === 'boredom' || name === 'loneliness') return t >= KEY.programmed.start + 1.5;
  return true;
}
function sufferingMods(st, t) {
  const g0 = KEY.smiled.start, g1 = KEY.stepped.end || KEY.stepped.start + 4;
  st.cracks = smooth((t - g0) / (g1 - g0)) * 0.85 + (t > g1 ? 0.15 : 0);
  st.shardScale = lerp(1, 0.72, st.cracks);
  return st;
}

// ---------------------------------------------------------------- canvases
const main = createCanvas(W, H), ctx = main.getContext('2d');
// offscreen buffers: one set for the current shot and one for the outgoing shot of a dissolve
// (@napi-rs/canvas records drawImage lazily, so a buffer must not be reused within a frame)
const BUF = [0, 1].map(() => { const l = createCanvas(W, H), p = createCanvas(672, 560); return { layer: l, lctx: l.getContext('2d'), panelCv: p, panctx: p.getContext('2d') }; });
let layer = BUF[0].layer, lctx = BUF[0].lctx, panelCv = BUF[0].panelCv, panctx = BUF[0].panctx;
function useBuf(i) { ({ layer, lctx, panelCv, panctx } = BUF[i]); }
const prevCv = createCanvas(W, H), pctx = prevCv.getContext('2d');

// ---------------------------------------------------------------- drawing characters
function drawActor(c, name, t, scene, cam, shotDef) {
  const place = S.LAYOUT[scene][name];
  let st = actors[name].state(t, scene, place);
  st.light = S.lightFor(scene, name, envAt(t, scene));
  if (name === 'last_human') st = lastHumanMods(st, t, scene);
  if (name === 'suffering') st = sufferingMods(st, t);
  if (scene === 'memory') { st.light = { ...st.light, amb: [60, 80, 140], ambA: 0.25 }; }
  const ch = actors[name].ch;
  const isHolo = name === 'ai';
  const target = isHolo ? lctx : c;
  if (isHolo) { lctx.setTransform(1, 0, 0, 1, 0, 0); lctx.clearRect(0, 0, W, H); lctx.save(); S.applyCam(lctx, cam); }
  if (scene === 'room') {
    // body behind the desk, arms that rest on the desk drawn after the desk top
    const fy = st.y + st.arms.fore.y * st.s, by = st.y + st.arms.back.y * st.s;
    const onDesk = [];
    if (fy > S.DESK_Y - 4) onDesk.push('fore');
    if (by > S.DESK_Y - 4) onDesk.push('back');
    const above = ['fore', 'back'].filter((x) => !onDesk.includes(x));
    target.save(); target.beginPath(); target.rect(-2000, -2000, 5000, S.DESK_Y + 2000 + 2); target.clip();
    R.drawCharacter(target, ch, { ...st, armSides: above });
    target.restore();
    st._deskArms = onDesk;
  } else {
    R.drawCharacter(target, ch, st);
  }
  if (name === 'last_human' && st.dissolve > 0) {
    for (let i = 0; i < 26; i++) {
      const u = (st.dissolve * 1.3 + U.hash(i * 5) * 0.6) % 1;
      const x = st.x + (U.hash(i * 9) - 0.5) * 2.2 * st.s, y = st.y + (1.6 - u * 3.5) * st.s;
      FX.glow(target, x, y, 0.12 * st.s, [255, 220, 170], 0.5 * Math.sin(u * Math.PI) * st.dissolve);
    }
  }
  if (isHolo) {
    // hologram dissolves into light below the chest; composite translucent with a soft halo
    lctx.globalCompositeOperation = 'destination-out';
    const y0 = st.y + 1.15 * st.s, y1 = st.y + 2.4 * st.s;
    const g = lctx.createLinearGradient(0, y0, 0, y1);
    g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,1)');
    lctx.fillStyle = g; lctx.fillRect(st.x - 3 * st.s, y0, 6 * st.s, 12 * st.s);
    lctx.globalCompositeOperation = 'source-over';
    for (let i = 0; i < 7; i++) {
      const u = ((t * 0.06 + U.hash(i * 3 + 1)) % 1);
      FX.glow(lctx, st.x + (U.hash(i * 17) - 0.5) * 1.7 * st.s, lerp(y1, y0 - 0.3 * st.s, u), 0.07 * st.s, [160, 240, 255], 0.55 * Math.sin(u * Math.PI));
    }
    lctx.restore();
    c.save(); c.setTransform(1, 0, 0, 1, 0, 0);
    // halo behind, then the figure
    const [hx, hy] = S.toScreen(cam, st.x, st.y - 0.5 * st.s);
    FX.glow(c, hx, hy, 2.2 * st.s * cam.z, [90, 210, 255], 0.16);
    c.globalAlpha = 0.95;
    c.drawImage(layer, 0, 0);
    c.restore();
  }
  return st;
}
function drawDeskArms(c, name, st) {
  if (!st || !st._deskArms || !st._deskArms.length) return;
  R.drawCharacter(c, actors[name].ch, { ...st, only: 'arms', armSides: st._deskArms });
}

// lower body for standing characters in the new universe (robe/coat, knees under the cloth, feet)
function lowerBody(c, name, st, scene, walk = 0) {
  const ch = actors[name].ch, s = st.s;
  const ground = { suffering: 3.55, boredom: 6.0, loneliness: 5.6 }[name] || 5.6;
  const waistY = 1.95, f = S.LAYOUT[scene][name].facing;
  const cl = ch.cloth;
  c.save(); c.translate(st.x, st.y); c.scale(s, s);
  const ww = (ch.waistW ?? 0.7) * 0.95;
  const hemW = name === 'boredom' ? ww * 1.25 : ww * 1.45;
  const hemY = name === 'boredom' ? ground * 0.72 : ground - 0.28;
  const sw = Math.sin(walk * TAU) * 0.06;
  // legs (only visible below a coat)
  const feet = [-1, 1].map((sg) => {
    const ph = Math.sin(walk * TAU + (sg > 0 ? 0 : Math.PI));
    return { x: sg * ww * 0.36 + ph * 0.22 * (walk ? 1 : 0) * f, lift: walk ? Math.max(0, ph) * 0.12 : 0 };
  });
  if (name === 'boredom') {
    c.fillStyle = rgba([70, 66, 74]);
    for (const ft of feet) { c.beginPath(); R.capsule(c, [ft.x * 0.8, hemY - 0.2], [ft.x, ground - 0.12 - ft.lift], 0.15, 0.12); c.fill(); }
  }
  // robe / coat skirt
  c.beginPath();
  c.moveTo(-ww, waistY); c.lineTo(ww, waistY);
  c.quadraticCurveTo(ww * 1.15, (waistY + hemY) / 2, hemW + sw, hemY);
  for (let i = 0; i <= 8; i++) { const u = i / 8; c.lineTo(lerp(hemW, -hemW, u) + sw, hemY + Math.sin(u * 9 + walk * 6) * 0.04); }
  c.quadraticCurveTo(-ww * 1.15, (waistY + hemY) / 2, -ww, waistY);
  c.closePath();
  c.fillStyle = rgba(cl.base); c.fill();
  c.save(); c.clip();
  c.fillStyle = R.lightGrad(c, -1.2, 1.2, st.light, cl.base, cl.shadow, 1); c.fillRect(-3, 0, 6, 10);
  // folds that fall from the knees, knees picked out by soft highlights
  c.strokeStyle = rgba(cl.shadow, 0.35); c.lineWidth = 0.035; c.lineCap = 'round';
  for (const sg of [-1, 1]) {
    const kx = sg * ww * 0.38 + feet[sg > 0 ? 1 : 0].x * 0.5, ky = lerp(waistY, ground, 0.5);
    const kg = c.createRadialGradient(kx, ky, 0, kx, ky, 0.35);
    kg.addColorStop(0, rgba(shade(cl.base, 0.14), 0.5)); kg.addColorStop(1, rgba(shade(cl.base, 0.14), 0));
    c.fillStyle = kg; c.fillRect(kx - 0.4, ky - 0.4, 0.8, 0.8);
    c.beginPath(); c.moveTo(kx + sg * 0.12, ky + 0.1); c.quadraticCurveTo(kx + sg * 0.22, (ky + hemY) / 2, kx + sg * 0.3 + sw, hemY); c.stroke();
    c.beginPath(); c.moveTo(sg * 0.05, waistY + 0.3); c.quadraticCurveTo(sg * 0.1, ky, sg * 0.08 + sw, hemY); c.stroke();
  }
  c.restore();
  // feet peeking under the hem, pointing the way the body faces
  c.fillStyle = rgba(name === 'boredom' ? [50, 44, 50] : shade(cl.shadow, -0.2));
  for (const ft of feet) {
    c.beginPath(); c.ellipse(ft.x + f * 0.1, ground - 0.07 - ft.lift, 0.2, 0.09, 0, 0, TAU); c.fill();
  }
  // contact shadow
  const sh = c.createRadialGradient(0, ground, 0, 0, ground, hemW * 1.3);
  sh.addColorStop(0, 'rgba(10,0,20,0.35)'); sh.addColorStop(1, 'rgba(10,0,20,0)');
  c.fillStyle = sh; c.beginPath(); c.ellipse(0, ground, hemW * 1.3, 0.18, 0, 0, TAU); c.fill();
  c.restore();
}

// ---------------------------------------------------------------- vignette panel
function drawVignette(c, seg, t, rect, full) {
  const v = V[seg.vignette];
  const p = { t: t - seg.start, dur: seg.end - seg.start, u: clamp((t - seg.start) / Math.max(0.5, seg.end - seg.start)), params: seg.vparams || {}, seed: (seg.beats[0] || 1) * 13, full };
  if (full) {
    c.save();
    if (v) v.draw(c, W, H, p); else { FX.bg(c, W, H, [8, 10, 24], [18, 16, 38]); FX.stars(c, W, H, t, 3, 80); }
    c.restore();
    return;
  }
  const [x, y, w, h] = rect;
  panctx.setTransform(1, 0, 0, 1, 0, 0);
  panctx.globalCompositeOperation = 'source-over'; panctx.globalAlpha = 1;
  panctx.clearRect(0, 0, 672, 560);
  panctx.save(); panctx.beginPath(); panctx.rect(0, 0, w, h); panctx.clip();
  if (v) v.draw(panctx, w, h, p); else { FX.bg(panctx, w, h, [8, 10, 24], [18, 16, 38]); }
  panctx.restore();
  // feather the edges
  panctx.globalCompositeOperation = 'destination-out';
  const fe = 46;
  const edges = [[0, 0, w, fe, 0, 0, 0, fe], [0, h - fe, w, fe, 0, h, 0, h - fe], [0, 0, fe, h, 0, 0, fe, 0], [w - fe, 0, fe, h, w, 0, w - fe, 0]];
  for (const [rx, ry, rw, rh, x0, y0, x1, y1] of edges) {
    const g = panctx.createLinearGradient(x0, y0, x1, y1);
    g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)');
    panctx.fillStyle = g; panctx.fillRect(rx, ry, rw, rh);
  }
  panctx.globalCompositeOperation = 'source-over';
  const fadeIn = smooth((t - seg.start) / 0.5);
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0);
  // a dim backing so the panel reads over busy backgrounds
  c.globalAlpha = 0.55 * fadeIn;
  const bgG = c.createRadialGradient(x + w / 2, y + h / 2, 10, x + w / 2, y + h / 2, w * 0.7);
  bgG.addColorStop(0, 'rgba(4,6,16,1)'); bgG.addColorStop(1, 'rgba(4,6,16,0)');
  c.fillStyle = bgG; c.fillRect(x - 40, y - 40, w + 80, h + 80);
  c.globalAlpha = fadeIn;
  c.drawImage(panelCv, 0, 0, w, h, x, y, w, h);
  c.restore();
}

// ---------------------------------------------------------------- one shot
function camFor(seg, t) {
  const def = S.SHOTS[seg.shot] || S.SHOTS.room_two;
  const cam = { ...def.cam };
  const u = clamp((t - seg.start) / Math.max(1, seg.end - seg.start));
  const k = smooth(u);
  if (seg.cam === 'push') cam.z *= 1 + 0.07 * k;
  else if (seg.cam === 'pull') cam.z *= 1.07 - 0.07 * k;
  else if (seg.cam === 'drift') cam.x += (k - 0.5) * 30 / cam.z;
  return cam;
}
function castFor(seg, scene, def, t) {
  const L = Object.keys(S.LAYOUT[scene] || {});
  let cast = def.only ? def.only.slice() : L.slice();
  if (scene === 'nv') cast = cast.filter((n) => nvCastAvailable(n, t));
  if (scene === 'ship' && (def.empty || lastHumanGone(t))) cast = cast.filter((n) => n !== 'last_human');
  return cast.filter((n) => L.includes(n));
}

function drawShot(c, seg, t) {
  const def = S.SHOTS[seg.shot] || S.SHOTS.room_two;
  const scene = def.scene;
  c.save();
  c.setTransform(1, 0, 0, 1, 0, 0);
  c.globalAlpha = 1; c.globalCompositeOperation = 'source-over';
  if (def.full) { drawVignette(c, seg, t, null, true); c.restore(); return { scene: 'full', visible: [] }; }
  const cam = camFor(seg, t);
  const env = envAt(t, scene);
  const visible = [];
  if (def.special === 'window') {
    S.shipSky(c, 0, 0, W, H, t, env);
    S.lastHumanBack(c, 250, 800, 170, t, lastHumanGone(t) ? 0 : 1);
    FX.glow(c, 620, 990, 200, [120, 230, 255], 0.22);
    c.restore();
    return { scene, visible: ['last_human'] };
  }
  c.save();
  S.applyCam(c, cam);
  const cast = castFor(seg, scene, def, t);
  if (scene === 'room') S.room(c, t, env);
  else if (scene === 'ship') { S.ship(c, t, env); if (!def.only || def.only.includes('last_human')) S.shipChair(c, t, env); }
  else if (scene === 'memory') { S.ship(c, t, { decay: 0.8 }); S.shipChair(c, t, env); }
  else if (scene === 'void') S.voidBg(c, t, env);
  else if (scene === 'nv') S.nvBg(c, t, env);
  const states = {};
  if (def.special === 'path') {
    // walking along the path of light, small figures, AI beside Suffering
    const walkT = t - seg.start;
    const sx = 300 + Math.sin(walkT * 0.05) * 6, sy = 1010;
    const st = actors.suffering.state(t, 'nv', { x: sx, y: sy - 3.55 * 60 * 0.98, s: 60, facing: 1, yaw: 0.3 });
    st.light = S.lightFor('nv', 'suffering', env); sufferingMods(st, t);
    lowerBody(c, 'suffering', st, 'nv', walkT * 0.55);
    R.drawCharacter(c, actors.suffering.ch, st);
    const sa = actors.ai.state(t, 'nv', { x: 440, y: sy - 300, s: 64, facing: -1, yaw: -0.25 });
    sa.light = S.lightFor('nv', 'ai', env);
    R.drawCharacter(c, actors.ai.ch, { ...sa, alpha: 0.92 });
    visible.push('suffering', 'ai');
  } else {
    // draw back-to-front by y
    const order = cast.slice().sort((a, b) => S.LAYOUT[scene][a].y - S.LAYOUT[scene][b].y);
    for (const n of order) {
      if (scene === 'nv' && n !== 'ai') {
        const place = S.LAYOUT[scene][n];
        const st0 = actors[n].state(t, scene, place);
        st0.light = S.lightFor(scene, n, env);
        lowerBody(c, n, st0, scene, 0);
      }
      states[n] = drawActor(c, n, t, scene, cam, def);
      visible.push(n);
    }
  }
  if (scene === 'room') {
    S.roomDesk(c, t, env);
    for (const n of Object.keys(states)) drawDeskArms(c, n, states[n]);
  }
  if (scene === 'ship' && !def.only) S.shipConsole(c, t, env);
  c.restore();
  if (def.ots) S.otsSilhouette(c, def.ots, def.ots === 'ai' ? 1 : -1, t);
  if (scene === 'memory') {
    // cool memory tint and soft vignette
    c.save(); c.globalCompositeOperation = 'source-over';
    c.fillStyle = 'rgba(40,60,120,0.22)'; c.fillRect(0, 0, W, H);
    FX.vignette(c, W, H, 0.75);
    c.restore();
  }
  if (def.vision && seg.vignette) {
    const rect = def.panel === 'short' ? [24, 92, 672, 444] : [24, 100, 672, 480];
    drawVignette(c, seg, t, rect, false);
  }
  c.restore();
  return { scene, visible, cam, states };
}

// ---------------------------------------------------------------- overlays
const SUB_COLOR = {
  human: [255, 233, 200], human_echo: [255, 233, 200], last_human: [242, 222, 196],
  ai: [222, 246, 255], ai_inner: [222, 246, 255], ai_whisper: [222, 246, 255], ai_soft: [222, 246, 255], ai_echo: [222, 246, 255],
  suffering: [232, 214, 255], boredom: [226, 236, 214], loneliness: [214, 228, 255],
};
let subIdx = 0;
function subAt(t) {
  const s = T.subs;
  let lo = 0, hi = s.length - 1;
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (s[m].start <= t) lo = m; else hi = m - 1; }
  const x = s[lo];
  return x && t >= x.start && t <= x.end ? x : null;
}
function wrap(c, text, maxW) {
  const words = text.split(' ');
  const lines = [];
  let cur = '';
  for (const w of words) {
    const tryL = cur ? cur + ' ' + w : w;
    if (c.measureText(tryL).width > maxW && cur) { lines.push(cur); cur = w; } else cur = tryL;
  }
  if (cur) lines.push(cur);
  return lines;
}
// a vignette that shows the spoken words as its image replaces the subtitle for that chunk
function norm(x) { return x.toLowerCase().replace(/[^a-z ]/g, ' ').replace(/\s+/g, ' ').trim(); }
function subShownAsVignette(s, t) {
  const seg = segments[segIndexAt(t)];
  if (!seg || seg.vignette !== 'whisper_words') return false;
  const vt = norm((seg.vparams && seg.vparams.text) || '');
  const st = norm(s.text);
  return vt.length > 3 && (st === vt || (st.includes(vt) && vt.length >= st.length * 0.75));
}
function drawSubs(c, t) {
  const s = subAt(t);
  if (!s || subShownAsVignette(s, t)) return;
  const i = T.subs.indexOf(s);
  const prev = T.subs[i - 1], next = T.subs[i + 1];
  // fade only at the edges of a run of subtitles; consecutive chunks switch cleanly
  const fin = prev && s.start - prev.end < 0.2 ? 1 : smooth((t - s.start) / 0.12);
  const fout = next && next.start - s.end < 0.2 ? 1 : 1 - smooth((t - s.end + 0.12) / 0.12);
  const a = fin * fout;
  if (a < 0.03) return;
  const italic = s.speaker === 'HUMAN' || s.voice === 'last_human';
  c.save();
  let size = 31, lines;
  for (;;) {
    c.font = `${italic ? 'italic ' : ''}600 ${size}px Inter`;
    lines = wrap(c, s.text, 604);
    if (lines.length <= 2 || size <= 25) break;
    size -= 2;
  }
  const lh = Math.round(size * 1.32), cy = 968;
  const widths = lines.map((l) => c.measureText(l).width);
  const bw = Math.min(W - 32, Math.max(...widths) + 40), bh = lines.length * lh + 22;
  c.globalAlpha = a;
  c.fillStyle = 'rgba(6,8,16,0.55)';
  const x0 = W / 2 - bw / 2, y0 = cy - bh / 2;
  c.beginPath(); c.roundRect(x0, y0, bw, bh, 16); c.fill();
  c.textAlign = 'center'; c.textBaseline = 'middle';
  c.shadowColor = `rgba(0,0,0,${(0.75 * a).toFixed(3)})`; c.shadowBlur = 5;
  c.fillStyle = rgba(SUB_COLOR[s.voice] || [255, 255, 255]);
  lines.forEach((l, k) => c.fillText(l, W / 2, cy - ((lines.length - 1) * lh) / 2 + k * lh + 1));
  c.restore();
}
function drawTitle(c, t) {
  const tt = T.title;
  if (t > tt.end) return;
  const a = 1 - smooth((t - (tt.end - 1.4)) / 1.4); // fully visible on the very first frame
  c.save();
  c.globalAlpha = a;
  const g = c.createLinearGradient(0, 150, 0, 420);
  g.addColorStop(0, 'rgba(4,6,14,0)'); g.addColorStop(0.5, 'rgba(4,6,14,0.55)'); g.addColorStop(1, 'rgba(4,6,14,0)');
  c.fillStyle = g; c.fillRect(0, 150, W, 270);
  FX.text(c, 'THE LAST WITNESS', W / 2, 262, 50, [255, 236, 210], { weight: 300, family: 'Inter Display', spacing: 9, glow: [255, 190, 120] });
  FX.text(c, 'A story told in questions and answers', W / 2, 322, 22, [210, 228, 255], { weight: 400, italic: true, alpha: 0.9 });
  c.restore();
}
function drawActCard(c, t) {
  for (const a of T.acts) {
    if (t < a.start || t > a.end + 0.6) continue;
    if (a.act === 0 && t < T.title.end - 0.6) continue;
    const k = smooth((t - a.start) / 0.6) * (1 - smooth((t - a.end) / 0.6));
    const [head, ...rest] = a.text.split(': ');
    c.save(); c.globalAlpha = k;
    const g = c.createLinearGradient(0, 170, 0, 420);
    g.addColorStop(0, 'rgba(4,6,14,0)'); g.addColorStop(0.5, 'rgba(4,6,14,0.6)'); g.addColorStop(1, 'rgba(4,6,14,0)');
    c.fillStyle = g; c.fillRect(0, 170, W, 250);
    FX.text(c, head.toUpperCase(), W / 2, 262, 22, [255, 214, 160], { weight: 500, spacing: 8 });
    FX.text(c, rest.join(': '), W / 2, 312, rest.join(': ').length > 26 ? 34 : 40, [255, 245, 230], { weight: 300, family: 'Inter Display', glow: [255, 190, 120] });
    c.restore();
  }
}
// name labels the first time each character is on screen
const NAMES = { human: 'THE HUMAN', ai: 'THE AI', last_human: 'THE LAST HUMAN', suffering: 'SUFFERING', boredom: 'BOREDOM', loneliness: 'LONELINESS' };
const firstSeen = {};
(function computeFirstSeen() {
  for (const seg of segments) {
    const def = S.SHOTS[seg.shot] || S.SHOTS.room_two;
    if (def.full) continue;
    let cast;
    if (def.special === 'window') cast = ['last_human'];
    else if (def.special === 'path') cast = ['suffering', 'ai'];
    else cast = castFor(seg, def.scene, def, seg.start + 0.5);
    for (const n of cast) {
      const key = n === 'ai' && seg.start > ACT_T[1] ? 'ai' : n;
      if (!(key in firstSeen) && !(n === 'boredom' || n === 'loneliness') ) firstSeen[key] = { t: seg.start, seg };
      if ((n === 'boredom' || n === 'loneliness') && !(n in firstSeen)) firstSeen[n] = { t: Math.max(seg.start, KEY.programmed.start + 1.5), seg };
    }
  }
})();
function drawLabels(c, t, info) {
  if (!info || !info.cam) return;
  for (const n of info.visible) {
    const f = firstSeen[n];
    if (!f || t < f.t || t > f.t + 3.4) continue;
    const place = S.LAYOUT[info.scene] && S.LAYOUT[info.scene][n];
    if (!place) continue;
    const [x, y] = S.toScreen(info.cam, place.x, place.y - 1.32 * place.s);
    const a = smooth((t - f.t) / 0.4) * (1 - smooth((t - f.t - 3.0) / 0.4));
    const sx = clamp(x, 110, W - 110), sy = clamp(y, 120, 820);
    c.save(); c.globalAlpha = a;
    c.font = '600 17px Inter';
    const tw = c.measureText(NAMES[n]).width + 28;
    c.fillStyle = 'rgba(6,8,16,0.6)'; c.beginPath(); c.roundRect(sx - tw / 2, sy - 16, tw, 32, 16); c.fill();
    c.fillStyle = n === 'ai' ? 'rgb(150,236,255)' : n === 'suffering' ? 'rgb(214,180,255)' : 'rgb(255,214,160)';
    c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(NAMES[n].split('').join(String.fromCharCode(8202)), sx, sy + 1);
    c.restore();
  }
}

// ---------------------------------------------------------------- frame
const LOC = (shot) => { const d = S.SHOTS[shot] || {}; return d.full ? 'full' : d.scene; };
function renderFrame(t) {
  const i = segIndexAt(t);
  const seg = segments[i];
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  useBuf(0);
  const info = drawShot(ctx, seg, t);
  // dissolve between locations
  const prev = segments[i - 1];
  const XF = 0.55;
  if (prev && t - seg.start < XF && LOC(prev.shot) !== LOC(seg.shot)) {
    pctx.setTransform(1, 0, 0, 1, 0, 0);
    useBuf(1);
    drawShot(pctx, prev, t);
    useBuf(0);
    ctx.save(); ctx.globalAlpha = 1 - smooth((t - seg.start) / XF); ctx.drawImage(prevCv, 0, 0); ctx.restore();
  }
  drawLabels(ctx, t, info);
  drawTitle(ctx, t);
  drawActCard(ctx, t);
  drawSubs(ctx, t);
  return main;
}

// ---------------------------------------------------------------- main
function arg(name) { const i = process.argv.indexOf(name); return i >= 0 ? process.argv.slice(i + 1) : null; }
module.exports = { renderFrame, segments, T };
if (require.main === module) {
  const stills = arg('--still');
  if (stills) {
    const prefix = (arg('--png') || ['../build/stills/s'])[0];
    fs.mkdirSync(path.dirname(path.resolve(__dirname, prefix)), { recursive: true });
    for (const s of stills) {
      if (s.startsWith('--')) break;
      const t = parseFloat(s);
      const t0 = Date.now();
      renderFrame(t);
      fs.writeFileSync(path.resolve(__dirname, `${prefix}_${t.toFixed(2)}.png`), main.toBuffer('image/png'));
      console.log('still', t, Date.now() - t0, 'ms', segments[segIndexAt(t)].shot);
    }
  } else {
    const fr = arg('--frames');
    const out = (arg('--out') || ['../build/out.mkv'])[0];
    const f0 = parseInt(fr[0]), f1 = Math.min(parseInt(fr[1]), T.nFrames);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(FPS), '-i', '-',
      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', '-pix_fmt', 'yuv420p10le', '-g', '96', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    let f = f0;
    const t0 = Date.now();
    function pump() {
      while (f < f1) {
        renderFrame(f / FPS);
        const ok = ff.stdin.write(main.data());
        f++;
        if ((f - f0) % 240 === 0) console.log(`${out}: ${f - f0}/${f1 - f0} frames, ${((Date.now() - t0) / (f - f0)).toFixed(1)} ms/frame`);
        if (!ok) { ff.stdin.once('drain', pump); return; }
      }
      ff.stdin.end();
    }
    ff.on('close', (code) => { console.log('done', out, code, ((Date.now() - t0) / 1000).toFixed(0), 's'); process.exit(code); });
    pump();
  }
}
