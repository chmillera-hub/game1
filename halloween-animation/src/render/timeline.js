// Turns script items + measured speech into time-keyed tracks.
const { clamp, lerp, ease, rng } = require('./lib');
const { exParams } = require('./face');

function build(script, lines) {
  const byIdx = {};
  lines.forEach((l) => (byIdx[l.idx] = l));
  const recs = [];
  let t = 0;
  script.items.forEach((it, i) => {
    const r = { i, it, t0: t };
    if (it.type === 'line') {
      const L = byIdx[i];
      if (!L) throw new Error('missing speech for item ' + i);
      r.L = L; r.s = t + (it.pre || 0); r.dur = L.dur; r.speechEnd = r.s + L.dur; r.e = r.speechEnd + (it.post ?? 0.25);
    } else { r.s = t; r.dur = it.dur; r.speechEnd = t + it.dur; r.e = t + it.dur; }
    t = r.e;
    recs.push(r);
  });
  const total = t;

  const resolve = (at, r) => {
    if (at === undefined || at === null) return r.s;
    if (typeof at === 'number') return at < 0 ? r.e + at : r.s + at;
    if (at === 'end') return r.speechEnd;
    if (at === 'start') return r.t0;
    if (at.endsWith('%')) return r.s + (parseFloat(at) / 100) * r.dur;
    if (at.startsWith('w:')) {
      const w = at.slice(2).toLowerCase();
      const c = r.L && r.L.cues.find((c) => c.word.toLowerCase() === w);
      if (!c) throw new Error(`cue ${at} not found in item ${r.i}`);
      return r.s + c.t;
    }
    throw new Error('bad at ' + at);
  };

  const tracks = {}; // name -> [{t, v, tr, ease}]
  const key = (name, t, v, tr, e) => (tracks[name] = tracks[name] || []).push({ t, v, tr, ease: e || 'soft' });
  const exKeys = {}, poseKeys = {}, lookKeys = {}, blinks = {};
  const camKeys = [];
  const music = [], sfx = [], speech = [], cues = [];

  for (const r of recs) {
    const it = r.it;
    if (it.cam) {
      if (it.cam.set || it.cam.at) camKeys.push({ t: r.t0, set: it.cam.set, pos: it.cam.at, cut: it.cam.cut ?? true });
      if (it.cam.to) camKeys.push({ t: r.e, pos: it.cam.to, ease: it.cam.ease || 'inout' });
    }
    for (const k of it.camKeys || []) camKeys.push({ t: resolve(k.at, r), pos: k.pos, cut: !!k.cut, ease: k.ease || 'inout' });
    for (const v of it.vars || []) {
      const tt = resolve(v.at, r);
      for (const [k, val] of Object.entries(v)) if (!['at', 'tr', 'ease'].includes(k)) key('V.' + k, tt, val, v.tr ?? 0.5, v.ease);
    }
    for (const a of it.acts || []) {
      const tt = resolve(a.at, r), w = a.who, tr = a.tr ?? 0.4;
      if (a.ex) (exKeys[w] = exKeys[w] || []).push({ t: tt, v: exParams(a.ex), tr, ease: 'soft' });
      if (a.pose) (poseKeys[w] = poseKeys[w] || []).push({ t: tt, name: a.pose, tr: a.tr ?? 0.5, ease: 'soft' });
      if (a.look) (lookKeys[w] = lookKeys[w] || []).push({ t: tt, target: a.look, tr });
      if (a.blink) (blinks[w] = blinks[w] || []).push({ t: tt, d: 0.42 });
      if (a.ex && tr > 0.2) (blinks[w] = blinks[w] || []).push({ t: tt + 0.03, d: 0.17, soft: true });
      for (const k of ['x', 'y', 'vis', 'climb', 'sitDown', 's']) if (a[k] !== undefined) key(w + '.' + k, tt, a[k], tr, 'soft');
    }
    if (it.music) music.push({ t: r.t0, mood: it.music });
    for (const s of it.sfx || []) sfx.push({ t: resolve(s.at, r), name: s.name });
    if (it.type === 'line') {
      const who = script.mouthOf[it.who];
      speech.push({ idx: r.i, who: it.who, char: who, s: r.s, e: r.speechEnd, env: r.L.env, cent: r.L.cent, wav: r.L.wav, motif: !!it.motif,
        sentences: r.L.sentences.map((x) => ({ text: x.text, s: r.s + x.start, e: r.s + x.end })),
        cues: r.L.cues.map((c) => ({ word: c.word, kind: c.kind, t: r.s + c.t })) });
      for (const c of r.L.cues) if (c.kind !== 'mark') cues.push({ t: r.s + c.t, kind: c.kind, word: c.word, motif: !!it.motif });
    }
  }
  const byT = (a, b) => a.t - b.t;
  for (const k in tracks) tracks[k].sort(byT);
  for (const w in exKeys) exKeys[w].sort(byT);
  for (const w in poseKeys) poseKeys[w].sort(byT);
  for (const w in lookKeys) lookKeys[w].sort(byT);
  camKeys.sort(byT);

  // automatic blinks + saccades per character
  const auto = {};
  ['pip', 'patch', 'bram', 'rattle', 'clatter', 'owl'].forEach((w, n) => {
    const r = rng(101 + n * 17);
    const list = (blinks[w] || []).slice();
    for (let tt = r() * 2; tt < total; tt += 2.2 + r() * 3.4) list.push({ t: tt, d: 0.16 });
    list.sort(byT);
    const sacc = [];
    for (let tt = 0; tt < total; tt += 0.6 + r() * 1.4) sacc.push({ t: tt, x: (r() - 0.5) * 0.16, y: (r() - 0.5) * 0.1 });
    auto[w] = { blinks: list, sacc };
  });
  // listener nods at sentence ends
  const sentenceEnds = [];
  for (const sp of speech) for (const s of sp.sentences) sentenceEnds.push({ t: s.e, who: sp.char });

  return { recs, total, tracks, exKeys, poseKeys, lookKeys, camKeys, music, sfx, speech, cues, auto, sentenceEnds };
}

// value at time T for numeric keys
function evalNum(keys, T, def) {
  if (!keys || !keys.length) return def;
  let v = def;
  for (let i = 0; i < keys.length; i++) {
    const k = keys[i];
    if (k.t > T) break;
    const nx = keys[i + 1];
    const endT = nx && nx.t <= T ? nx.t : T;
    const u = k.tr > 0 ? clamp((endT - k.t) / k.tr) : 1;
    v = lerp(v, k.v, ease[k.ease || 'soft'](u));
  }
  return v;
}

function evalObj(keys, T, def) {
  if (!keys || !keys.length) return { ...def };
  let v = { ...(keys[0].v || def) };
  for (let i = 0; i < keys.length; i++) {
    const k = keys[i];
    if (k.t > T) break;
    const nx = keys[i + 1];
    const endT = nx && nx.t <= T ? nx.t : T;
    const u = ease[k.ease || 'soft'](k.tr > 0 ? clamp((endT - k.t) / k.tr) : 1);
    const nv = {};
    for (const p in k.v) nv[p] = lerp(v[p] ?? k.v[p], k.v[p], u);
    v = nv;
  }
  return v;
}

function evalCam(camKeys, T) {
  let set = null, k = null, idx = -1;
  for (let i = 0; i < camKeys.length; i++) {
    if (camKeys[i].t > T) break;
    idx = i;
    if (camKeys[i].set) set = camKeys[i].set;
  }
  if (idx < 0) { k = camKeys[0]; return { set: k.set, x: k.pos[0], y: k.pos[1], z: k.pos[2] }; }
  // find last key with a position at or before idx
  let a = idx; while (a > 0 && !camKeys[a].pos) a--;
  const A = camKeys[a];
  const B = camKeys[idx + 1];
  let p = A.pos;
  if (B && !B.cut && B.pos && !B.set) {
    const u = ease[B.ease || 'inout'](clamp((T - A.t) / Math.max(1e-3, B.t - A.t)));
    p = [lerp(A.pos[0], B.pos[0], u), lerp(A.pos[1], B.pos[1], u), lerp(A.pos[2], B.pos[2], u)];
  }
  return { set, x: p[0], y: p[1], z: p[2], segStart: A.t };
}

module.exports = { build, evalNum, evalObj, evalCam };
