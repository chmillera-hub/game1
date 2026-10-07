// Core helpers: math, easing, timeline access, blinking, gaze, captions.
const W = 1920, H = 1080;
const TL = window.TIMELINE;
const FPS = TL.fps;

const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const easeOut = (t) => 1 - Math.pow(1 - clamp(t), 3);
const easeIn = (t) => Math.pow(clamp(t), 3);
const easeInOut = (t) => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const back = (t) => { t = clamp(t); const c = 1.70158; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
// progress 0..1 between a and b
const prog = (t, a, b) => clamp((t - a) / (b - a));
const ramp = (t, a, b, f = smooth) => f(prog(t, a, b));
// value that rises a->b then falls c->d
const pulse = (t, a, b, c, d) => ramp(t, a, b) * (1 - ramp(t, c, d));

const BEATS = {};
TL.beats.forEach(b => BEATS[b.label] = b);
const SCENES = {};
TL.scenes.forEach(s => SCENES[s.id] = s);
const bs = (l) => BEATS[l].start;
const be = (l) => BEATS[l].end;
// time at a fraction through a beat (for word-level cues)
const bf = (l, f) => lerp(BEATS[l].start, BEATS[l].end, f);

function lineAt(t) {
  for (const b of TL.beats) if (b.type === 'line' && t >= b.start && t < b.end) return b;
  return null;
}
function mouthOf(name, t) {
  const b = lineAt(t);
  if (!b || b.speaker !== name || b.thought) return 0;
  const f = Math.floor(t * FPS);
  return TL.mouth[f] || 0;
}
function speaking(name, t) {
  const b = lineAt(t);
  return !!(b && b.speaker === name && !b.thought);
}
// most recent non-narrator speaker at time t (for gaze)
function lastSpeaker(t, exclude) {
  let who = null, when = -1;
  for (const b of TL.beats) {
    if (b.type !== 'line' || b.start > t) continue;
    if (b.speaker === 'narr' || b.thought || b.speaker === exclude) continue;
    if (b.start > when) { when = b.start; who = b.speaker; }
  }
  return { who, when };
}

// deterministic random
function mulberry(seed) {
  return function () {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
const hashStr = (s) => { let h = 2166136261; for (const c of s) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; };

const BLINKS = {};
function blinkOf(name, t, slow = 1) {
  if (!BLINKS[name]) {
    const r = mulberry(hashStr(name)); const list = []; let x = r() * 2;
    while (x < TL.duration + 10) { list.push(x); x += 2.2 + r() * 3.6; if (r() < .15) { list.push(x); x += .3; } }
    BLINKS[name] = list;
  }
  const d = 0.17 * slow;
  for (const b of BLINKS[name]) {
    if (t < b) break;
    if (t < b + d) { const p = (t - b) / d; return p < .4 ? p / .4 : 1 - (p - .4) / .6; }
  }
  return 0;
}

// gaze vector (-1..1) from a head position toward a target; eases between
// targets so eyes travel like a quick saccade rather than snapping.
function gazeVec(from, to, max = 1) {
  const dx = to[0] - from[0], dy = to[1] - from[1];
  const d = Math.hypot(dx, dy) || 1;
  const k = Math.min(1, d / 240) * max;
  return [dx / d * k, dy / d * k * .8];
}
// piecewise gaze schedule: [[time, [x,y] | 'speaker'], ...]
function gazeSchedule(t, schedule, from, positions, self) {
  const resolve = (tgt, tt) => {
    if (tgt === 'speaker') {
      const { who } = lastSpeaker(tt, self);
      return who && positions[who] ? positions[who] : null;
    }
    return tgt;
  };
  let cur = null, prev = null, tc = -99;
  for (const [ts, tgt] of schedule) { if (t >= ts) { prev = cur; cur = [ts, tgt]; } }
  if (!cur) return [0, 0];
  const a = prev ? resolve(prev[1], cur[0] - .01) : null;
  const bpos = resolve(cur[1], t);
  if (!bpos) return [0, 0];
  const gb = gazeVec(from, bpos);
  // speaker-following gaze: re-saccade when the speaker changes
  if (cur[1] === 'speaker') {
    const { who, when } = lastSpeaker(t, self);
    const lag = .12 + (hashStr(self) % 7) * .03;
    const startT = Math.max(when + lag, cur[0]);
    const before = lastSpeaker(startT - lag - .02, self);
    const pa = before.who && positions[before.who] ? gazeVec(from, positions[before.who]) : gb;
    const k = smooth(prog(t, startT, startT + .14));
    return [lerp(pa[0], gb[0], k), lerp(pa[1], gb[1], k)];
  }
  if (!a) return gb;
  const ga = gazeVec(from, a);
  const k = smooth(prog(t, cur[0], cur[0] + .16));
  return [lerp(ga[0], gb[0], k), lerp(ga[1], gb[1], k)];
}

// tiny idle motion
const breathe = (t, seed = 0, rate = 1) => Math.sin(t * 1.9 * rate + seed);
