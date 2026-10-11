// Per-character animation state: tracks set by the direction, plus the
// automatic "life" layers (blinks, saccades, breathing, talk motion, lip-sync).

const { Track, Steps, clamp, lerp, ease, fbm, mulberry32 } = require('./core');
const { CHARACTERS, VISEMES, SEAT_HIP_Y } = require('./rig');

const DEFAULTS = {
  x: 540, sit: 1, walk: 0, lean: 0, slump: 0, shoulder: 0, laugh: 0, breathAmp: 1,
  headTurn: 0, headTilt: 0, headPitch: 0, headShift: 0,
  nodP: 0, shakeT: 0,
  browL: 0, browR: 0, angL: 0, angR: 0, furrow: 0,
  lidU: 0.12, lidL: 0, lidTilt: 0, lidDiff: 0,
  smile: 0.05, mouthW: 1, mouthOpen: 0, smirk: 0, press: 0, blush: 0, tear: 0,
  talkAnim: 1,
  lx: -0.22, ly: 1.06, rx: 0.22, ry: 1.06, lfs: 0, rfs: 0, lhx: -0.6, lhy: 1, rhx: 0.6, rhy: 1,
  propX: 0, propY: 0.7,
};

// Expression presets (face + a little posture)
const EXPR = {
  neutral: { browL: 0, browR: 0, angL: 0, angR: 0, furrow: 0, lidU: 0.12, lidL: 0, lidTilt: 0, smile: 0.05, mouthOpen: 0, smirk: 0, press: 0 },
  focused: { browL: -0.15, browR: -0.15, angL: -0.25, angR: -0.25, furrow: 0.55, lidU: 0.26, lidL: 0.2, lidTilt: 0, smile: 0, mouthOpen: 0, smirk: 0, press: 0.5 },
  focusTongue: { browL: 0.05, browR: -0.2, angL: -0.1, angR: -0.3, furrow: 0.5, lidU: 0.24, lidL: 0.25, smile: 0.1, smirk: 0.35, press: 0 },
  excited: { browL: 0.55, browR: 0.55, angL: 0.1, angR: 0.1, furrow: 0, lidU: 0.0, lidL: 0.1, smile: 0.55, mouthOpen: 0.12, smirk: 0, press: 0 },
  dismay: { browL: 0.35, browR: 0.35, angL: 0.6, angR: 0.6, furrow: 0.1, lidU: 0.15, lidL: 0.05, smile: -0.35, mouthOpen: 0.1, smirk: 0, press: 0 },
  selfLaugh: { browL: 0.3, browR: 0.3, angL: 0.45, angR: 0.45, furrow: 0, lidU: 0.25, lidL: 0.45, smile: 0.6, mouthOpen: 0.05, smirk: 0.1, press: 0 },
  happy: { browL: 0.25, browR: 0.25, angL: 0.1, angR: 0.1, furrow: 0, lidU: 0.1, lidL: 0.4, lidTilt: 0, smile: 0.8, mouthOpen: 0.0, smirk: 0, press: 0 },
  grin: { browL: 0.3, browR: 0.5, angL: 0.05, angR: 0.05, furrow: 0, lidU: 0.12, lidL: 0.35, smile: 0.9, mouthOpen: 0.04, smirk: 0.3, press: 0 },
  laugh: { browL: 0.45, browR: 0.45, angL: 0.25, angR: 0.25, furrow: 0, lidU: 0.3, lidL: 0.7, lidTilt: 0, smile: 1.0, mouthOpen: 0.32, smirk: 0, press: 0 },
  smileFade: { browL: 0.0, browR: 0.0, angL: 0.25, angR: 0.25, furrow: 0, lidU: 0.22, lidL: 0.1, smile: 0.12, mouthOpen: 0, smirk: 0.1, press: 0 },
  hurt: { browL: -0.05, browR: -0.05, angL: 0.55, angR: 0.55, furrow: 0.1, lidU: 0.4, lidL: 0.05, lidTilt: 0.3, smile: -0.22, mouthOpen: 0, smirk: 0, press: 0.2 },
  frozen: { browL: 0.5, browR: 0.5, angL: 0.1, angR: 0.1, furrow: 0, lidU: -0.05, lidL: 0.15, lidTilt: 0, smile: 0.45, mouthOpen: 0.08, smirk: 0.15, press: 0 },
  uneasy: { browL: 0.3, browR: 0.3, angL: 0.55, angR: 0.55, furrow: 0.1, lidU: 0.08, lidL: 0, lidTilt: 0, smile: -0.1, mouthOpen: 0, smirk: 0, press: 0.5 },
  awkward: { browL: 0.25, browR: 0.35, angL: 0.45, angR: 0.45, furrow: 0, lidU: 0.15, lidL: 0.1, smile: 0.25, mouthOpen: 0, smirk: 0.35, press: 0.4 },
  worried: { browL: 0.25, browR: 0.25, angL: 0.7, angR: 0.7, furrow: 0.15, lidU: 0.1, lidL: 0, lidTilt: 0.1, smile: -0.2, mouthOpen: 0, smirk: 0, press: 0.2 },
  defensive: { browL: -0.3, browR: -0.25, angL: -0.6, angR: -0.6, furrow: 0.8, lidU: 0.28, lidL: 0.15, lidTilt: 0, smile: -0.35, mouthOpen: 0, smirk: -0.1, press: 0.4 },
  confused: { browL: 0.5, browR: -0.15, angL: 0.15, angR: -0.2, furrow: 0.35, lidU: 0.14, lidL: 0.12, lidTilt: 0, smile: -0.12, mouthOpen: 0, smirk: -0.2, press: 0 },
  calm: { browL: 0.0, browR: 0.0, angL: 0.18, angR: 0.18, furrow: 0, lidU: 0.2, lidL: 0.05, lidTilt: 0, smile: 0.0, mouthOpen: 0, smirk: 0, press: 0.15 },
  firm: { browL: -0.05, browR: -0.05, angL: 0.05, angR: 0.05, furrow: 0.2, lidU: 0.16, lidL: 0.1, lidTilt: 0, smile: -0.05, mouthOpen: 0, smirk: 0, press: 0.3 },
  gentle: { browL: 0.18, browR: 0.18, angL: 0.38, angR: 0.38, furrow: 0, lidU: 0.18, lidL: 0.15, lidTilt: 0.05, smile: 0.22, mouthOpen: 0, smirk: 0, press: 0 },
  sad: { browL: -0.05, browR: -0.05, angL: 0.6, angR: 0.6, furrow: 0.1, lidU: 0.36, lidL: 0.05, lidTilt: 0.35, smile: -0.32, mouthOpen: 0, smirk: 0, press: 0.15 },
  guilty: { browL: -0.12, browR: -0.12, angL: 0.5, angR: 0.5, furrow: 0.15, lidU: 0.38, lidL: 0.08, lidTilt: 0.3, smile: -0.25, mouthOpen: 0, smirk: 0, press: 0.35 },
  thinking: { browL: 0.3, browR: 0.02, angL: 0.1, angR: -0.05, furrow: 0.25, lidU: 0.2, lidL: 0.15, lidTilt: 0, smile: -0.05, mouthOpen: 0, smirk: -0.25, press: 0.4 },
  sheepish: { browL: 0.22, browR: 0.3, angL: 0.42, angR: 0.42, furrow: 0, lidU: 0.2, lidL: 0.2, lidTilt: 0, smile: 0.35, mouthOpen: 0, smirk: 0.4, press: 0.2 },
  amused: { browL: 0.3, browR: 0.3, angL: 0.2, angR: 0.2, furrow: 0, lidU: 0.15, lidL: 0.45, lidTilt: 0, smile: 0.72, mouthOpen: 0, smirk: 0.1, press: 0 },
  deadpan: { browL: 0.0, browR: 0.0, angL: 0.0, angR: 0.0, furrow: 0, lidU: 0.36, lidL: 0.1, lidTilt: 0, smile: 0.0, mouthOpen: 0, smirk: 0, press: 0.35 },
  earnest: { browL: 0.35, browR: 0.35, angL: 0.35, angR: 0.35, furrow: 0, lidU: 0.05, lidL: 0.05, lidTilt: 0, smile: 0.0, mouthOpen: 0, smirk: 0, press: 0.1 },
  wideEyed: { browL: 0.8, browR: 0.8, angL: 0.25, angR: 0.25, furrow: 0, lidU: -0.08, lidL: 0, lidTilt: 0, smile: -0.08, mouthOpen: 0.05, smirk: 0, press: 0 },
  warm: { browL: 0.2, browR: 0.2, angL: 0.32, angR: 0.32, furrow: 0, lidU: 0.16, lidL: 0.32, lidTilt: 0.05, smile: 0.5, mouthOpen: 0, smirk: 0, press: 0 },
  sincere: { browL: 0.12, browR: 0.12, angL: 0.42, angR: 0.42, furrow: 0.05, lidU: 0.14, lidL: 0.1, lidTilt: 0.05, smile: 0.08, mouthOpen: 0, smirk: 0, press: 0.1 },
  skeptical: { browL: 0.7, browR: -0.15, angL: 0.1, angR: -0.25, furrow: 0.1, lidU: 0.3, lidL: 0.2, lidTilt: 0, smile: 0.12, mouthOpen: 0, smirk: 0.35, press: 0.2 },
  relieved: { browL: 0.2, browR: 0.2, angL: 0.35, angR: 0.35, furrow: 0, lidU: 0.25, lidL: 0.3, lidTilt: 0.1, smile: 0.4, mouthOpen: 0, smirk: 0, press: 0 },
  braced: { browL: 0.15, browR: 0.15, angL: 0.3, angR: 0.3, furrow: 0.2, lidU: 0.18, lidL: 0.1, lidTilt: 0, smile: -0.1, mouthOpen: 0, smirk: 0, press: 0.55 },
  stunned: { browL: 0.35, browR: 0.35, angL: 0.45, angR: 0.45, furrow: 0, lidU: 0.05, lidL: 0, lidTilt: 0, smile: -0.1, mouthOpen: 0.06, smirk: 0, press: 0 },
  proud: { browL: 0.15, browR: 0.25, angL: 0.0, angR: 0.0, furrow: 0, lidU: 0.3, lidL: 0.25, lidTilt: 0, smile: 0.35, mouthOpen: 0, smirk: 0.3, press: 0.2 },
};

// Arm poses: hand targets in torso space, normalized by shoulder width / torso height.
const POSES = {
  lap: { l: [-0.22, 1.06], r: [0.22, 1.06] },
  controller: { l: [-0.17, 0.72], r: [0.17, 0.72], prop: 'controller', propAt: [0, 0.72] },
  controllerUp: { l: [-0.17, 0.6], r: [0.17, 0.6], prop: 'controller', propAt: [0, 0.6] },
  controllerDrop: { l: [-0.22, 0.92], r: [0.2, 0.9], prop: 'controller', propAt: [0, 0.92] },
  knees: { l: [-0.3, 1.02], r: [0.3, 1.02] },
  clasped: { l: [-0.06, 0.88], r: [0.06, 0.9], shape: 'fist' },
  crossed: { l: [0.22, 0.42], r: [-0.22, 0.47], lh: [-1, 0.2], rh: [1, 0.2], shape: 'fist' },
  neckRub: { l: [-0.24, 0.95], r: [0.12, -0.22], rh: [1, -1.3] },
  gestureR: { l: [-0.22, 1.06], r: [0.2, 0.56], fs: [0, 0.35] },
  gestureL: { l: [-0.2, 0.56], r: [0.22, 1.06], fs: [0.35, 0] },
  openBoth: { l: [-0.24, 0.58], r: [0.24, 0.58], fs: [0.35, 0.35] },
  shrug: { l: [-0.48, 0.44], r: [0.48, 0.44], fs: [0.35, 0.35] },
  fistR: { l: [-0.24, 0.95], r: [0.72, 0.42], shape: 'fist' },
  fistL: { l: [-0.72, 0.42], r: [0.24, 0.95], shape: 'fist' },
  chest: { l: [-0.22, 1.06], r: [0.04, 0.32], fs: [0, 0.45] },
  chinR: { l: [-0.15, 0.9], r: [0.05, -0.1], rh: [1, 1], front: 'r' },
  faceRub: { l: [-0.24, 0.95], r: [0.0, -0.33], rh: [1, 1], front: 'r' },
  mug: { l: [-0.08, 0.7], r: [0.12, 0.62], prop: 'mug', propAt: [0.08, 0.58] },
  mugLap: { l: [-0.12, 0.86], r: [0.14, 0.82], prop: 'mug', propAt: [0.06, 0.8] },
  sip: { l: [-0.24, 0.95], r: [0.12, -0.18], rh: [1, 1], front: 'r', prop: 'mugFace', propAt: [0.1, -0.2] },
  plate: { l: [-0.2, 0.58], r: [0.2, 0.58], prop: 'plate', propAt: [0, 0.55] },
  plateLap: { l: [-0.24, 0.86], r: [0.24, 0.86], prop: 'plate', propAt: [0, 0.84] },
  hang: { l: [-0.56, 0.9], r: [0.56, 0.9] },
  touchR: { l: [-0.56, 0.9], r: [0.86, 0.98] },
  wave: { l: [-0.56, 0.9], r: [0.62, -0.25], rh: [1, 0.6] },
  pointSelf: { l: [-0.22, 1.06], r: [0.0, 0.36], shape: 'fist', fs: [0, 0.45] },
  handUp: { l: [-0.22, 1.06], r: [0.16, 0.4], fs: [0, 0.5] },
};

class Puppet {
  constructor(name, x, seed) {
    this.name = name;
    this.ch = CHARACTERS[name];
    this.seed = seed;
    this.T = {};
    for (const [k, v] of Object.entries(DEFAULTS)) this.T[k] = new Track(v);
    this.T.x = new Track(x);
    this.gaze = new Steps({ target: 'cam', dur: 0.2, head: 0.6, ox: 0, oy: 0 });
    this.shapeL = new Steps('open'); this.shapeR = new Steps('open');
    this.frontL = new Steps(false); this.frontR = new Steps(false);
    this.propS = new Steps(null);
    this.lines = []; this.vocals = [];
    this.blinks = [];
    this.forcedBlinks = [];
    this.noBlink = []; // [t0, t1] windows (eyes closed / staring)
    this.visible = new Steps(true);
  }

  finalize(duration) {
    const rnd = mulberry32(this.seed * 7919 + 13);
    let t = rnd() * 2;
    while (t < duration) {
      this.blinks.push(t);
      if (rnd() < 0.12) this.blinks.push(t + 0.32);
      t += 2.0 + rnd() * 3.6;
    }
    // blink on big gaze shifts
    const ks = this.gaze.keys;
    for (let i = 1; i < ks.length; i++) {
      if (ks[i].v.target !== ks[i - 1].v.target && ks[i].v.blink !== false) this.blinks.push(ks[i].t + 0.01);
    }
    this.blinks.push(...this.forcedBlinks);
    this.blinks = this.blinks.filter((b) => !this.noBlink.some(([a, c]) => b > a - 0.25 && b < c));
    this.blinks.sort((a, b) => a - b);
    // saccade schedule
    this.sacc = [];
    t = 0;
    while (t < duration) {
      this.sacc.push([t, (rnd() * 2 - 1) * 0.07, (rnd() * 2 - 1) * 0.05]);
      t += 0.5 + rnd() * 1.4;
    }
  }

  blinkAt(t) {
    let v = 0;
    for (const b of this.blinks) {
      if (b > t) break;
      const d = t - b;
      if (d < 0.07) v = Math.max(v, d / 0.07);
      else if (d < 0.1) v = 1;
      else if (d < 0.23) v = Math.max(v, 1 - (d - 0.1) / 0.13);
    }
    return v;
  }

  saccAt(t) {
    let lo = 0, hi = this.sacc.length - 1;
    while (lo < hi) { const m = (lo + hi + 1) >> 1; if (this.sacc[m][0] <= t) lo = m; else hi = m - 1; }
    const cur = this.sacc[lo], prev = this.sacc[Math.max(lo - 1, 0)];
    const f = clamp((t - cur[0]) / 0.05, 0, 1);
    return [lerp(prev[1], cur[1], f), lerp(prev[2], cur[2], f)];
  }

  talkState(t) {
    for (const ln of this.lines) {
      if (t >= ln.start - 0.02 && t < ln.end + 0.08) {
        // viseme
        const cues = ln.cues;
        let i = 0;
        while (i + 1 < cues.length && cues[i + 1][0] <= t) i++;
        const cur = VISEMES[cues[i][1]] || VISEMES.X;
        const prev = VISEMES[cues[Math.max(i - 1, 0)][1]] || VISEMES.X;
        const f = clamp((t - cues[i][0]) / 0.06, 0, 1);
        const V = {};
        for (const k of ['open', 'width', 'round', 'tt', 'tb', 'tongue', 'press', 'fv', 'lift']) {
          V[k] = lerp(prev[k] || 0, cur[k] || 0, f);
        }
        const fi = Math.floor((t - ln.start) * 24);
        let e = 0, n = 0;
        for (let j = fi - 2; j <= fi + 2; j++) if (j >= 0 && j < ln.env.length) { e += ln.env[j]; n++; }
        return { V, env: n ? e / n : 0, line: ln };
      }
    }
    return null;
  }

  vocalState(t) {
    for (const v of this.vocals) {
      if (t >= v.start && t < v.end) {
        const fi = Math.floor((t - v.start) * 24);
        return { env: v.env[Math.min(fi, v.env.length - 1)] || 0 };
      }
    }
    return null;
  }

  resolveGaze(g, t, world) {
    const me = this.T.x.at(t);
    let r = { gx: 0, gy: 0, turn: 0, pitch: 0 };
    const tgt = g.target;
    if (world.puppets[tgt]) {
      const ox = world.puppets[tgt].T.x.at(t);
      const dx = ox - me;
      r = { gx: clamp(dx / 260, -1, 1) * 0.8, gy: 0.05, turn: clamp(dx / 620, -0.55, 0.55), pitch: 0 };
    } else {
      const table = {
        cam: [0, 0, 0, 0], tv: [0, 0.12, 0, 0.05], down: [0, 0.8, 0, 0.38],
        downL: [-0.55, 0.75, -0.18, 0.3], downR: [0.55, 0.75, 0.18, 0.3],
        left: [-0.85, 0.05, -0.38, 0], right: [0.85, 0.05, 0.38, 0],
        upL: [-0.7, -0.55, -0.25, -0.15], upR: [0.7, -0.55, 0.25, -0.15], up: [0, -0.7, 0, -0.18],
        hands: [0, 0.85, 0, 0.42], window: [-0.85, -0.3, -0.42, -0.08],
        lap: [0, 0.9, 0, 0.45],
      };
      const v = table[tgt] || table.cam;
      r = { gx: v[0], gy: v[1], turn: v[2], pitch: v[3] };
    }
    const hw = g.head === undefined ? 0.6 : g.head;
    return { gx: clamp(r.gx + (g.ox || 0), -1, 1), gy: clamp(r.gy + (g.oy || 0), -1, 1), turn: r.turn * hw, pitch: r.pitch * hw };
  }

  evaluate(t, world) {
    const T = this.T;
    const P = {};
    for (const k of Object.keys(T)) P[k] = T[k].at(t);
    const seed = this.seed;

    // gaze
    const { cur, prev } = this.gaze.keyAt(t);
    const a = this.resolveGaze(prev.v, t, world), b = this.resolveGaze(cur.v, t, world);
    const f = ease.inOut(clamp((t - cur.t) / (cur.v.dur || 0.2), 0, 1));
    const fh = ease.inOut(clamp((t - cur.t) / ((cur.v.dur || 0.2) * 1.8), 0, 1)); // head lags the eyes
    const [sx, sy] = this.saccAt(t);
    P.gx = lerp(a.gx, b.gx, f) + sx;
    P.gy = lerp(a.gy, b.gy, f) + sy;
    const gTurn = lerp(a.turn, b.turn, fh), gPitch = lerp(a.pitch, b.pitch, fh);

    // talking / laughing
    const talk = this.talkState(t);
    const voc = this.vocalState(t);
    const env = talk ? talk.env : 0;
    const ta = P.talkAnim;

    P.headTurn = P.headTurn + gTurn + P.shakeT + 0.025 * fbm(t * 0.23, seed) + (talk ? 0.02 * fbm(t * 1.1, seed + 5) * ta : 0);
    P.headPitch = P.headPitch + gPitch + P.nodP + 0.03 * fbm(t * 0.2, seed + 2) - env * 0.1 * ta;
    P.headTilt = P.headTilt + 0.018 * fbm(t * 0.27, seed + 3) + (talk ? 0.03 * fbm(t * 0.9, seed + 7) * ta : 0);
    P.browL += env * 0.22 * ta; P.browR += env * 0.22 * ta;
    P.breath = Math.sin(t * Math.PI * 2 / 4.1 + seed) * P.breathAmp;

    // laugh shake: from the laugh track and from any laugh vocal
    const lshake = Math.max(P.laugh, voc ? voc.env : 0);
    P.bob = -lshake * 5 * Math.abs(Math.sin(t * Math.PI * 2 * 4.2));
    P.walkPhase = t * Math.PI * 2 * 1.7;
    P.bob += -P.walk * 7 * Math.abs(Math.sin(P.walkPhase));

    // eyes
    const blink = this.blinkAt(t);
    const lid = P.lidU + Math.max(0, P.headPitch) * 0.12;
    const closeTo = (v) => v + (1 - Math.max(v, 0)) * blink;
    P.lidUL = closeTo(lid - P.lidDiff);
    P.lidUR = closeTo(lid + P.lidDiff);

    // mouth
    const M = { open: P.mouthOpen, width: P.mouthW, round: 0, smile: P.smile, smirk: P.smirk, tt: 0, tb: 0, tongue: 0, press: P.press, fv: 0, lift: 0 };
    if (talk) {
      const V = talk.V;
      M.open = Math.max(V.open * 1.1 * (1 - P.mouthOpen * 0.5) + P.mouthOpen * 0.4, 0);
      M.width = V.width * P.mouthW;
      M.round = V.round; M.tt = V.tt; M.tb = V.tb; M.tongue = V.tongue; M.fv = V.fv; M.lift = V.lift;
      M.press = Math.max(V.press, 0);
      M.smile = P.smile * 0.65;
    }
    if (voc) {
      M.open = Math.max(M.open, 0.12 + voc.env * 0.55);
      M.tt = 1; M.smile = Math.max(M.smile, 0.7);
    } else if (P.laugh > 0.05 && !talk) {
      M.open = Math.max(M.open, P.laugh * (0.18 + 0.2 * Math.abs(Math.sin(t * Math.PI * 2 * 4.2))));
      M.tt = 1;
    }
    P.mouth = M;

    // arms
    const ch = this.ch;
    P.armL = { x: P.lx * ch.shoulderW, y: P.ly * ch.torsoH, hx: P.lhx, hy: P.lhy, fs: P.lfs, shape: this.shapeL.at(t), front: this.frontL.at(t) };
    P.armR = { x: P.rx * ch.shoulderW, y: P.ry * ch.torsoH, hx: P.rhx, hy: P.rhy, fs: P.rfs, shape: this.shapeR.at(t), front: this.frontR.at(t) };
    P.prop = this.propS.at(t);
    P.propPos = [P.propX * ch.shoulderW, P.propY * ch.torsoH];
    if (P.prop === 'mugFace') P.propPos = [P.armR.x + 4, P.armR.y - 6];
    P.visible = this.visible.at(t);
    return P;
  }

  head(t) {
    const P = { x: this.T.x.at(t), sit: this.T.sit.at(t), slump: this.T.slump.at(t) };
    const ch = this.ch;
    const hipY = SEAT_HIP_Y - (1 - P.sit) * 160;
    return [P.x, hipY - ch.torsoH - ch.neckLen - ch.headH * 0.47 + P.slump * 18];
  }
}

module.exports = { Puppet, EXPR, POSES, DEFAULTS };
