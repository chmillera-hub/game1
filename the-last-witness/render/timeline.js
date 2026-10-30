// Builds the absolute timeline (build/timeline.json) from beats, voice takes and direction:
// beat times, subtitle chunks, shot segments, vignette segments, per-character keyframes,
// music moods/cues with word times, and per-frame lip-sync tracks per speaking character.
'use strict';
const fs = require('fs');
const path = require('path');
const { visemeOf } = require('./lib/expr');

const ROOT = path.join(__dirname, '..');
const FPS = 24;
const LEAD_IN = 3.2;      // title over the opening scene before the first line
const ACT_CARD = 3.4;     // act title held over the scene
const OUTRO = 7.0;

const beats = JSON.parse(fs.readFileSync(path.join(ROOT, 'script/beats.json')));
const dirFiles = fs.readdirSync(path.join(ROOT, 'direction')).filter((f) => f.endsWith('.json'));
const dir = {};
for (const f of dirFiles) for (const d of JSON.parse(fs.readFileSync(path.join(ROOT, 'direction', f)))) dir[d.id] = d;

// custom vignettes requested by the directors, mapped onto implemented keys
const CUSTOM = {
  151: ['flower_of_light', {}], 208: ['alien_finds', { stage: 'handprint' }], 301: ['monument', { crumble: true }],
  338: ['questions_float', { text: '?', dissolve: true }], 418: ['kneel_among', {}],
  456: ['dance_with_shadow', { stage: 'talk' }], 457: ['dance_with_shadow', { stage: 'argue' }], 458: ['dance_with_shadow', { stage: 'dance' }],
  515: ['path_forward', { pair: true }], 527: ['stagnant_loop', {}], 528: ['shrink_dim', {}], 562: ['kneel_spark', {}],
};

const VOICE_SPEAKER = {
  human: 'human', human_echo: 'human', last_human: 'last_human', ai: 'ai', ai_inner: 'ai', ai_whisper: 'ai',
  ai_soft: 'ai', ai_echo: 'ai', suffering: 'suffering', boredom: 'boredom', loneliness: 'loneliness',
};
// lip amplitude by delivery
const VOICE_LIP = { ai_whisper: 0.6, ai_inner: 0.75, ai_echo: 0.8, last_human: 0.7, human_echo: 0.8, loneliness: 0.85 };

let t = LEAD_IN;
const out = { fps: FPS, beats: [], subs: [], acts: [], title: { start: 0, end: LEAD_IN + 1.5 } };
let lastDir = null;
for (const b of beats) {
  if (b.kind === 'act_card') {
    if (b.act > 0) { out.acts.push({ act: b.act, text: b.text, start: t, end: t + ACT_CARD }); t += ACT_CARD; }
    else out.acts.push({ act: 0, text: b.text, start: 1.2, end: LEAD_IN + 1.2 });
    continue;
  }
  const d = dir[b.id] || lastDir || { shot: 'room_two', chars: {} };
  lastDir = d;
  let vignette = d.vignette || null, vparams = d.vparams || {};
  if (vignette === 'custom' && CUSTOM[b.id]) [vignette, vparams] = CUSTOM[b.id];
  const rec = {
    id: b.id, act: b.act, kind: b.kind, speaker: b.speaker, voice: b.voice || null, text: b.text || '',
    start: t, shot: d.shot, cam: d.cam || 'hold', chars: d.chars || {}, vignette, vparams, music: d.music || {},
  };
  if (b.kind === 'emote') {
    rec.end = t + b.dur; rec.who = 'human';
    t = rec.end + 0.3;
  } else {
    const take = JSON.parse(fs.readFileSync(path.join(ROOT, 'build/tts', `beat_${String(b.id).padStart(4, '0')}.json`)));
    rec.dur = take.dur; rec.end = t + take.dur; rec.who = VOICE_SPEAKER[b.voice];
    rec.phonemes = take.phonemes;
    for (const c of take.chunks) out.subs.push({ text: c.text, start: t + c.start, end: t + c.end, voice: b.voice, speaker: b.speaker, beat: b.id });
    t = rec.end + (b.pause_after ?? 0.4);
  }
  out.beats.push(rec);
}
out.duration = t + OUTRO;
// hold the last subtitle chunks a touch longer for reading, never past the next one
for (let i = 0; i < out.subs.length; i++) {
  const nx = out.subs[i + 1];
  const want = out.subs[i].end + 0.35;
  out.subs[i].end = nx ? Math.min(want, nx.start - 0.02) : want;
}

// ---- shot segments (consecutive beats with the same shot+vignette merge; gaps belong to the previous beat)
const segs = [];
for (let i = 0; i < out.beats.length; i++) {
  const b = out.beats[i];
  const segStart = i === 0 ? 0 : b.start - 0.12; // cut slightly before the line
  const last = segs[segs.length - 1];
  const vkey = b.vignette ? b.vignette + JSON.stringify(b.vparams) : '';
  if (last && last.shot === b.shot && last.vkey === vkey) { last.beats.push(b.id); continue; }
  if (last) last.end = segStart;
  segs.push({ shot: b.shot, cam: b.cam, start: segStart, end: null, vignette: b.vignette, vparams: b.vparams, vkey, beats: [b.id], act: b.act });
}
segs[segs.length - 1].end = out.duration;
// act cards show the opening shot of the new act
for (const a of out.acts) {
  const s = segs.find((x) => x.start <= a.end && x.end > a.end) || segs.find((x) => x.start >= a.start);
  if (s && s.start > a.start) s.start = a.start;
  const prev = segs[segs.indexOf(s) - 1];
  if (prev) prev.end = s.start;
}
out.segments = segs.map(({ vkey, ...s }) => s);

// ---- music: moods carry forward; cues get word-level times
out.music = { moods: [], cues: [] };
let mood = null;
for (const b of out.beats) {
  const m = b.music || {};
  if (m.mood && m.mood !== mood) { mood = m.mood; out.music.moods.push({ t: b.start - 0.3, mood }); }
  if (m.cue && b.phonemes) {
    const word = m.cue.word.toLowerCase().replace(/[^a-z']/g, '');
    const text = b.text.toLowerCase();
    let idx = text.search(new RegExp(`\\b${word}`));
    if (idx < 0) idx = text.indexOf(word);
    const frac = idx < 0 ? 0.5 : idx / Math.max(1, text.length);
    const voiced = b.phonemes.filter((p) => p[0] !== ' ');
    const p = voiced[Math.min(voiced.length - 1, Math.floor(frac * voiced.length))];
    out.music.cues.push({ t: b.start + (p ? p[1] : b.dur * frac), kind: m.cue.kind, word: m.cue.word, beat: b.id, mood });
  }
}
if (!out.music.moods.length || out.music.moods[0].t > 0) out.music.moods.unshift({ t: 0, mood: out.music.moods[0]?.mood || 'intimate' });

// ---- lip-sync tracks: per speaking character, frame-sampled viseme [open, wide, round, teeth] + stress nods
const nFrames = Math.ceil(out.duration * FPS);
const lips = {};
const stress = {};
for (const b of out.beats) {
  if (!b.phonemes) continue;
  const who = b.who;
  if (!lips[who]) { lips[who] = new Float32Array(nFrames * 4); stress[who] = []; }
  const amp = VOICE_LIP[b.voice] ?? 1;
  const ph = b.phonemes;
  // per-phoneme target viseme (marks inherit the following phoneme)
  const vis = ph.map((p) => visemeOf(p[0]));
  for (let i = vis.length - 2; i >= 0; i--) if (!vis[i] && ph[i][0] !== ' ') vis[i] = vis[i + 1];
  for (let i = 0; i < ph.length; i++) if (ph[i][0] === 'ˈ') stress[who].push(b.start + ph[i][1]);
  const f0 = Math.floor(b.start * FPS), f1 = Math.ceil(b.end * FPS);
  for (let f = f0; f <= f1 && f < nFrames; f++) {
    const tl = f / FPS - b.start;
    // gaussian-weighted blend of visemes around this instant (stateless smoothing)
    let acc = [0, 0, 0, 0], wsum = 0;
    for (let i = 0; i < ph.length; i++) {
      const c = (ph[i][1] + ph[i][2]) / 2;
      const dt = c - (tl + 0.02); // lips lead the sound slightly
      if (dt < -0.12 || dt > 0.12) continue;
      const w = Math.exp(-(dt * dt) / (2 * 0.035 * 0.035));
      const v = vis[i] || [0, 0, 0, 0];
      for (let k = 0; k < 4; k++) acc[k] += v[k] * w;
      wsum += w;
    }
    if (wsum > 0) for (let k = 0; k < 4; k++) lips[who][f * 4 + k] = Math.max(lips[who][f * 4 + k], (acc[k] / Math.max(wsum, 0.6)) * (k === 0 ? amp : 1));
  }
}
const lipDir = path.join(ROOT, 'build/lips');
fs.mkdirSync(lipDir, { recursive: true });
for (const who of Object.keys(lips)) fs.writeFileSync(path.join(lipDir, `${who}.f32`), Buffer.from(lips[who].buffer));
out.stress = stress;
out.lipChars = Object.keys(lips);
out.nFrames = nFrames;
for (const b of out.beats) delete b.phonemes;
fs.writeFileSync(path.join(ROOT, 'build/timeline.json'), JSON.stringify(out));
console.log(`duration ${(out.duration / 60).toFixed(2)} min, ${nFrames} frames, ${out.segments.length} segments, ${out.subs.length} subs, ${out.music.cues.length} cues`);
