// Absolute timeline (build/timeline.json): beat times, subtitles, title cards, shot segments,
// the passengers' hummed song (notes), music moods and word-timed cues, and sound effects.
'use strict';
const fs = require('fs');
const path = require('path');
const DIR = require('./direction');

const ROOT = path.join(__dirname, '..');
const FPS = 24;
const LEAD = 3.6;      // title over the opening scene before the first line
const TITLE2 = 4.2;    // second part title held over its opening scene
const OUTRO = 5.5;

const beats = JSON.parse(fs.readFileSync(path.join(ROOT, 'script/beats.json')));
const out = { fps: FPS, beats: [], subs: [], titles: [], segments: [], song: [], music: { moods: [], cues: [] }, sfx: [] };
let t = 0;
for (const b of beats) {
  const d = DIR[b.id] || {};
  const rec = { id: b.id, kind: b.kind, part: b.part, text: b.text, start: t, dir: d };
  if (b.kind === 'title') {
    const dur = b.part === 0 ? LEAD : TITLE2;
    out.titles.push({ text: b.text, sound: b.sound, start: t, end: t + dur, part: b.part });
    rec.end = t + dur; rec.dur = dur; t = rec.end;
  } else {
    const take = JSON.parse(fs.readFileSync(path.join(ROOT, 'build/tts', `beat_${String(b.id).padStart(4, '0')}.json`)));
    rec.dur = take.dur; rec.end = t + take.dur; rec.phonemes = take.phonemes;
    for (const c of take.chunks) out.subs.push({ text: c.text, start: t + c.start, end: t + c.end, beat: b.id });
    t = rec.end + b.pause_after;
    rec.next = t;
  }
  out.beats.push(rec);
}
out.duration = t + OUTRO;
for (let i = 0; i < out.subs.length; i++) {
  const nx = out.subs[i + 1];
  out.subs[i].end = nx ? Math.min(out.subs[i].end + 0.35, nx.start - 0.02) : out.subs[i].end + 0.35;
}

// word time inside a beat from its phoneme timings
function wordTime(b, word) {
  const text = b.text.toLowerCase();
  let idx = text.search(new RegExp(`\\b${word.toLowerCase()}`));
  if (idx < 0) idx = Math.floor(text.length / 2);
  const frac = idx / Math.max(1, text.length);
  const voiced = (b.phonemes || []).filter((p) => p[0] !== ' ');
  const p = voiced[Math.min(voiced.length - 1, Math.floor(frac * voiced.length))];
  return b.start + (p ? p[1] : b.dur * frac);
}

// shot segments
for (const b of out.beats) {
  const shots = (b.dir.shots || [[0, 'interior', {}]]);
  shots.forEach(([f, shot, params], k) => {
    const start = b.kind === 'title' ? b.start : (k === 0 ? b.start - 0.15 : b.start + f * b.dur);
    out.segments.push({ shot, params: params || {}, start: Math.max(0, start), beat: b.id, part: b.part, crowd: b.dir.crowd, child: b.dir.child, spider: b.dir.spider });
  });
}
out.segments[0].start = 0;
for (let i = 0; i < out.segments.length; i++) out.segments[i].end = i + 1 < out.segments.length ? out.segments[i + 1].start : out.duration;

// music moods, cues, effects
let mood = null;
for (const b of out.beats) {
  const d = b.dir;
  if (d.mood && d.mood !== mood) { mood = d.mood; out.music.moods.push({ t: Math.max(0, b.start - 0.4), mood }); }
  if (d.cue && b.phonemes) out.music.cues.push({ t: wordTime(b, d.cue[0]), word: d.cue[0], kind: d.cue[1], beat: b.id, mood });
  for (const [f, name] of d.sfx || []) out.sfx.push({ t: b.start + f * b.dur, name, beat: b.id });
}

// the passengers' "merry song": an original, childish hummed melody, looping from its start
// cue until the word "cease"; louder while "the music is so very loud", slow and low while it drones
const A = [[60, 1], [64, 1], [67, 1], [67, 1], [69, 1], [67, 1], [64, 2], [62, 1], [62, 1], [64, 1], [65, 1], [64, 1], [62, 1], [60, 2]];
const B = [[67, 1], [67, 1], [69, 1], [67, 1], [65, 1], [64, 1], [62, 2], [64, 1], [65, 1], [67, 1], [64, 1], [62, 1], [60, 1], [60, 2]];
const songStart = out.sfx.find((s) => s.name === 'song_start').t;
const ceaseBeat = out.beats.find((b) => b.text.startsWith('One day, the singing will abruptly cease'));
const songEnd = wordTime(ceaseBeat, 'cease') + 0.05;
out.sfx.find((s) => s.name === 'song_stop').t = songEnd;
const loudBeat = out.beats.find((b) => b.text.startsWith('The music, you see, is so very loud'));
const droneBeat = out.beats.find((b) => b.text.startsWith('Inside, the song drones on'));
let st = songStart, k = 0;
while (st < songEnd) {
  const phrase = (Math.floor(k / A.length) % 2) ? B : A;
  const [midi, beatsLen] = phrase[k % A.length];
  const droning = st >= droneBeat.start - 0.3;
  const spb = droning ? 0.82 : 0.6;
  const loud = st >= loudBeat.start && st < loudBeat.end + 0.6;
  const dur = Math.min(beatsLen * spb, songEnd - st);
  out.song.push({ t: st, dur, midi: droning ? midi - 5 : midi, vel: loud ? 0.85 : droning ? 0.4 : 0.55 });
  st += beatsLen * spb; k++;
}
out.songEnd = songEnd;
out.nFrames = Math.ceil(out.duration * FPS);
for (const b of out.beats) delete b.phonemes;
fs.writeFileSync(path.join(ROOT, 'build/timeline.json'), JSON.stringify(out, null, 1));
console.log(`duration ${out.duration.toFixed(1)} s, ${out.nFrames} frames, ${out.segments.length} shots, ${out.subs.length} subs, ${out.song.length} song notes, ${out.music.cues.length} cues`);
