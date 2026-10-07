// Scene choreography. Everything is a pure function of time t (seconds).
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');
function begin() { ctx.setTransform(window.SCALE || 1, 0, 0, window.SCALE || 1, 0, 0); }

// keyframes: [[t, value], ...] (numbers or {x,y,z}); eased between keys
function kf(t, keys, f = easeInOut) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    if (t <= keys[i][0]) {
      const [t0, a] = keys[i - 1], [t1, b] = keys[i], k = f((t - t0) / (t1 - t0));
      if (typeof a === 'number') return lerp(a, b, k);
      const o = {}; for (const key in a) o[key] = lerp(a[key], b[key], k); return o;
    }
  }
  return keys[keys.length - 1][1];
}
// flip facing smoothly: returns {facing, turnSquash}
function turn(t, t0, from, dur = .32) {
  const k = easeInOut(prog(t, t0, t0 + dur));
  const v = lerp(from, -from, k);
  return { facing: v >= 0 ? 1 : -1, turnSquash: Math.max(.06, Math.abs(v)) };
}
function turns(t, start, times) {
  let f = start, out = { facing: start, turnSquash: 1 };
  for (const t0 of times) { if (t >= t0) { out = turn(t, t0, f); f = -f; } }
  return out;
}

const HEADS = {
  pooh: (o) => [o.x, o.y - 270 * (o.s || 1)],
  piglet: (o) => [o.x, o.y - 155 * (o.s || 1)],
  rabbit: (o) => [o.x, o.y - 245 * (o.s || 1)],
  owl: (o) => [o.x, o.y - 205 * (o.s || 1)],
  eeyore: (o) => [o.x + (o.facing || 1) * 190 * (o.s || 1), o.y - (262 - (o.headDrop ?? .5) * 45) * (o.s || 1)],
  bird: (o) => [o.x + (o.facing || 1) * 20 * (o.s || 1), o.y - 45 * (o.s || 1)],
};
// build a character state: auto blink + lip-sync + smoothed gaze
function mk(name, t, st, target) {
  const o = Object.assign({ t, blink: blinkOf(name, t, st.slowBlink || 1), mouth: mouthOf(name, t) * (st.mouthK || 1) }, st);
  if (target) {
    const h = HEADS[name](o);
    let gx = 0, gy = 0;
    for (let k = 0; k < 6; k++) { const p = target(t - k * .045); const g = gazeVec(h, p); gx += g[0] / 6; gy += g[1] / 6; }
    o.gx = gx * (o.facing || 1); o.gy = gy;
  }
  if (o.gxAdd) o.gx = (o.gx || 0) + o.gxAdd;
  o.bob = (o.bob || 0) - o.mouth * 3 + breathe(t, hashStr(name) % 7) * 1.5;
  return o;
}
// target = whoever is talking (or fallback)
function talkTarget(name, heads, fallback) {
  return (tt) => {
    const b = lineAt(tt) || lineAt(tt - .6);
    if (b && b.speaker !== name && heads[b.speaker]) return heads[b.speaker];
    return typeof fallback === 'function' ? fallback(tt) : fallback;
  };
}
const DRAW = { pooh: drawPooh, piglet: drawPiglet, rabbit: drawRabbit, owl: drawOwl, eeyore: drawEeyore, bird: drawBird };

function captionLayer(c, t) {
  const b = lineAt(t) || (() => {
    for (const x of TL.beats) if (x.type === 'line' && t >= x.end && t < x.end + .4) return x;
    return null;
  })();
  if (!b) return;
  const a = Math.min(ramp(t, b.start - .05, b.start + .12), 1 - ramp(t, b.end + .2, b.end + .4));
  caption(c, b.thought ? `(${b.caption})` : b.caption, a, b.thought, b.speaker);
}
function chapterLayer(c, t) {
  for (const s of TL.scenes) {
    if (!s.chapter) continue;
    if (t >= s.start && t < s.end) chapterCard(c, s.chapter, Math.min(ramp(t, s.start + .3, s.start + .9), 1 - ramp(t, s.start + 5.2, s.start + 5.9)));
  }
}
function sunbeam(c, x, a, t = 0) {
  if (a <= 0) return;
  c.save(); c.globalCompositeOperation = 'screen';
  for (let i = 0; i < 5; i++) {
    const w = 70 + i * 30, sx = x + i * 60 - 120 + Math.sin(t * .8 + i) * 15;
    const g = c.createLinearGradient(sx, 0, sx - 260, H);
    g.addColorStop(0, `rgba(255,236,170,${.22 * a})`); g.addColorStop(1, 'rgba(255,236,170,0)');
    c.fillStyle = g; c.beginPath(); c.moveTo(sx, -10); c.lineTo(sx + w, -10); c.lineTo(sx + w - 300, H); c.lineTo(sx - 300 - w * .4, H); c.fill();
  }
  c.restore();
}
function fadeBlack(c, a, col = '0,0,0') { if (a > 0) { c.fillStyle = `rgba(${col},${a})`; c.fillRect(0, 0, W, H); } }
function butterflies(c, t, cx, cy, n = 4, spread = 500) {
  for (let i = 0; i < n; i++) {
    const x = cx + Math.sin(t * .7 + i * 2.1) * spread * (.5 + i * .15), y = cy + Math.sin(t * 1.3 + i * 1.7) * 80 - i * 30;
    const fl = Math.abs(Math.sin(t * 16 + i));
    c.fillStyle = ['#f2c94c', '#e98a9a', '#ffffff', '#b9a2e6'][i % 4];
    c.save(); c.translate(x, y);
    c.beginPath(); c.ellipse(-7 * fl, 0, 9 * fl + 1, 7, -.4, 0, TAU); c.fill();
    c.beginPath(); c.ellipse(7 * fl, 0, 9 * fl + 1, 7, .4, 0, TAU); c.fill(); c.restore();
  }
}
function miniPasture(c, x, y, w, h, t, a) {
  c.save(); c.globalAlpha = a; ell(c, x, y, w * .44, h * .4); c.clip();
  const g = c.createLinearGradient(0, y - h / 2, 0, y + h / 2); g.addColorStop(0, '#8fcaf0'); g.addColorStop(1, '#fff3cf');
  c.fillStyle = g; c.fillRect(x - w, y - h, w * 2, h * 2);
  c.fillStyle = '#ffe58a'; c.beginPath(); c.arc(x + w * .22, y - h * .18, h * .1, 0, TAU); c.fill();
  c.fillStyle = '#9fd07a'; c.beginPath(); c.moveTo(x - w, y + h); c.lineTo(x - w, y + h * .05); c.quadraticCurveTo(x - w * .1, y - h * .12, x + w, y + h * .12); c.lineTo(x + w, y + h); c.fill();
  c.fillStyle = '#7fbf5a'; c.beginPath(); c.moveTo(x - w, y + h); c.lineTo(x - w, y + h * .25); c.quadraticCurveTo(x + w * .2, y + h * .05, x + w, y + h * .3); c.lineTo(x + w, y + h); c.fill();
  drawEeyore(c, { x: x - w * .05 + Math.sin(t * 2) * 10, y: y + h * .26, s: .16, gallop: 1, phase: t * 2.2, ears: 1, headDrop: .1, smile: .9, lid: 0, t, earFlap: 1 });
  c.restore();
}

// ---------------------------------------------------------------- clearing cast
const CL = { owl: [520, 905], rabbit: [760, 905], pooh: [1000, 905], piglet: [1200, 905], eeyore: [1480, 905] };

// ---------------------------------------------------------------- TITLE + S1 + S2 + S3 (clearing)
function sceneClearing(c, t) {
  const S1 = SCENES.s1, S2 = SCENES.s2, S3 = SCENES.s3;
  // ---------- camera
  const cam = kf(t, [
    [0, { x: 960, y: 330, z: 1.05 }], [3.4, { x: 1000, y: 580, z: 1 }], [5.5, { x: 1000, y: 580, z: 1 }], [6.8, { x: 1560, y: 650, z: 1.65 }],
    [S1.start, { x: 1560, y: 650, z: 1.65 }], [S1.start + .01, { x: 1080, y: 610, z: 1.02 }],
    [bs('s1e') + .3, { x: 1080, y: 610, z: 1.02 }], [be('s1e'), { x: 1400, y: 650, z: 1.55 }],
    [bs('s1f') - .2, { x: 1400, y: 640, z: 1.9 }], [be('s1g') + .3, { x: 1380, y: 640, z: 1.95 }],
    [S2.start, { x: 1340, y: 620, z: 1.35 }], [bs('crickets'), { x: 1290, y: 620, z: 1.3 }], [bs('crickets') + .01, { x: 1040, y: 610, z: 1.02 }],
    [bs('s2c'), { x: 1040, y: 610, z: 1.02 }], [be('s2e'), { x: 1000, y: 620, z: 1.12 }], [bs('s2f') + 1, { x: 1400, y: 560, z: 1.35 }],
    [be('s2g'), { x: 1430, y: 610, z: 1.4 }],
    [S3.start, { x: 1570, y: 600, z: 1.45 }], [bs('s3c'), { x: 1600, y: 600, z: 1.55 }], [be('s3c') + .3, { x: 1060, y: 610, z: 1.02 }],
    [bs('s3f'), { x: 1060, y: 610, z: 1.02 }], [be('s3f'), { x: 1450, y: 640, z: 1.5 }],
    [bs('s3g') - .12, { x: 1450, y: 640, z: 1.5 }], [bs('s3g') + .05, { x: 1420, y: 670, z: 2.05 }],
    [bs('s3h') + .2, { x: 1420, y: 670, z: 2.05 }], [bs('s3h') + 1.6, { x: 1040, y: 610, z: 1.02 }],
  ]);
  if (t > bs('s3g') && t < bs('s3g') + .5) { const k = 1 - prog(t, bs('s3g'), bs('s3g') + .5); cam.x += Math.sin(t * 90) * 8 * k; cam.y += Math.cos(t * 77) * 6 * k; }

  // ---------- Eeyore
  const eWalk = prog(t, 14.0, 15.9);
  const ex = t < S1.start ? 1680 : lerp(1680, 1550, easeInOut(eWalk));
  const eT = turns(t, -1, [bs('s3c') - 1.0, bs('s3f') - .5]);
  const sadBase = { ears: .05, headDrop: .82, lid: .5, browIn: .85, smile: -.4 };
  let E = Object.assign({}, sadBase);
  const hope1 = pulse(t, bs('s2a'), bs('s2a') + .8, bs('s2f') + 2.5, be('s2g'));
  E.ears = lerp(E.ears, .45, hope1); E.headDrop = lerp(E.headDrop, .35, hope1); E.lid = lerp(E.lid, .12, hope1); E.smile = lerp(E.smile, .05, hope1);
  E.browIn = lerp(E.browIn, .55, hope1);
  // s1g: exasperated side-glance
  const exas = pulse(t, bs('s1g') + .3, bs('s1g') + .8, be('s1g'), be('s1g') + .6);
  E.browAngry = .45 * exas; E.browIn -= .45 * exas; E.lid += .1 * exas;
  // bird gives hope -> joy
  const listen = ramp(t, bs('s3a') + .5, be('s3a'));
  const joy = ramp(t, be('s3b') + .2, be('s3b') + 1.6) * (1 - ramp(t, bs('s3f') - .5, bs('s3f')));
  E.ears = lerp(E.ears, .5, listen); E.lid = lerp(E.lid, .15, listen); E.headDrop = lerp(E.headDrop, .45, listen); E.browIn = lerp(E.browIn, .6, listen);
  E.ears = lerp(E.ears, 1, joy); E.lid = lerp(E.lid, 0, joy); E.headDrop = lerp(E.headDrop, .05, joy); E.smile = lerp(E.smile, .85, joy);
  E.browIn = lerp(E.browIn, .1, joy); E.sparkle = joy; E.tailWag = joy;
  // confrontation
  const mad = ramp(t, bs('s3f') - .5, bs('s3f') + .2) * (1 - ramp(t, bs('s3h') + .3, bs('s3h') + 2.2));
  E.ears = lerp(E.ears, -.5, mad); E.browAngry = Math.max(E.browAngry, .85 * mad); E.browIn = lerp(E.browIn, 0, mad); E.lid = lerp(E.lid, .22, mad);
  E.smile = lerp(E.smile, -.6, mad); E.headDrop = lerp(E.headDrop, .3, mad);
  const wtf = pulse(t, bs('s3g') - .1, bs('s3g'), be('s3g'), be('s3g') + .6);
  E.wide = .5 * wtf; E.browUp = wtf * .6;
  // deflate after
  const defl = ramp(t, bs('s3h') + .5, bs('s3h') + 2.5);
  E.desat = .22 * ramp(t, bs('s3i'), be('s3i'));
  // sigh in title
  const sigh = pulse(t, 7.2, 7.9, 7.9, 8.8);
  const eSt = Object.assign(E, { x: ex, y: 905, s: .85, ...eT, walk: eWalk > 0 && eWalk < 1 ? 1 : 0, phase: t * 1.25, sag: sigh * 6 - defl * 2, mouthK: .85 });
  if (t >= bs('s3g') && t < be('s3g')) eSt.mouthK = 1.2;

  // ---------- bird
  const birdLand = [ex - 10, 905 - 228 * .85];
  const bArrive = prog(t, S3.start + .4, S3.start + 2.0), bLeave = prog(t, be('s3c') + .1, be('s3c') + 1.5);
  let bird = null;
  if (t > S3.start + .3 && bLeave < 1) {
    let bx, by, flying = true;
    if (bArrive < 1) { const k = easeOut(bArrive); bx = lerp(2200, birdLand[0], k); by = lerp(150, birdLand[1], k) - Math.sin(k * Math.PI) * 120; }
    else if (bLeave > 0) { const k = easeIn(bLeave); bx = lerp(birdLand[0], 2300, k); by = lerp(birdLand[1], 100, k) - Math.sin(k * Math.PI) * 60; }
    else { bx = birdLand[0]; by = birdLand[1] - Math.abs(Math.sin(prog(t, bs('s3a'), bs('s3a') + .35) * Math.PI)) * 18; flying = false; }
    bird = { x: bx, y: by, s: 1.05, facing: bLeave > 0 ? 1 : -1, flap: flying };
  }

  // ---------- friends
  const heads = {};
  const fr = {
    owl: { x: CL.owl[0], y: CL.owl[1], s: .85, smile: .3 },
    rabbit: { x: CL.rabbit[0], y: CL.rabbit[1], s: .85, smile: .35 },
    pooh: { x: CL.pooh[0], y: CL.pooh[1], s: .85, smile: .5 },
    piglet: { x: CL.piglet[0], y: CL.piglet[1], s: .8, smile: .4 },
  };
  // title: happy picnic
  const happyTitle = 1 - ramp(t, 8, 9);
  fr.pooh.honey = t < S1.start || (t > bs('s1e') && t < S2.start);
  fr.pooh.armR = fr.pooh.honey ? .9 + Math.max(0, Math.sin(t * 2.2)) * .5 : .25;
  fr.pooh.smile = .6;
  fr.rabbit.bob = -Math.abs(Math.sin(t * 7)) * 6 * happyTitle; fr.piglet.bob = -Math.abs(Math.sin(t * 8 + 1)) * 8 * happyTitle;
  fr.owl.mouthAuto = happyTitle;
  // s1a Pooh waves at Eeyore
  const wave = pulse(t, bs('s1a') - .2, bs('s1a') + .2, be('s1a') + .2, be('s1a') + .6);
  if (wave > 0) { fr.pooh.armR = lerp(fr.pooh.armR, 2.35 + Math.sin(t * 13) * .3, wave); fr.pooh.smile = .8; }
  // s1b Piglet bounces
  const pb = pulse(t, bs('s1b') - .1, bs('s1b') + .1, be('s1b'), be('s1b') + .3);
  fr.piglet.bob = (fr.piglet.bob || 0) - Math.abs(Math.sin(t * 11)) * 14 * pb; fr.piglet.armL = .3 + 2 * pb; fr.piglet.armR = .3 + 2 * pb; fr.piglet.smile = .4 + .4 * pb;
  // s1c Rabbit proud
  const proud = pulse(t, bs('s1c') - .1, bs('s1c') + .4, be('s1d'), be('s1d') + .6);
  fr.rabbit.puff = 1 + .12 * proud; fr.rabbit.armR = .2 + 1.3 * proud * (t < be('s1c') ? 1 : .2); fr.rabbit.headTilt = -.08 * proud; fr.rabbit.smile = .35 + .35 * proud;
  fr.rabbit.lid = .35 * pulse(t, bs('s1c') + 1.5, bs('s1c') + 1.8, be('s1c'), be('s1c') + .3);
  // s1d Owl pats Rabbit on the back, everyone smug-happy
  const pat = pulse(t, bs('s1d') - .2, bs('s1d') + .3, be('s1d') + .3, be('s1d') + .8);
  fr.owl.wingR = pat * (1.1 + Math.sin(t * 10) * .25); fr.owl.smile = .3 + .4 * pat;
  const smug = pulse(t, bs('s1d'), bs('s1d') + .5, bs('s1e') + 1.5, bs('s1e') + 2.5);
  for (const k of ['owl', 'rabbit', 'pooh', 'piglet']) { fr[k].smile = Math.max(fr[k].smile, .75 * smug); fr[k].lid = Math.max(fr[k].lid || 0, .3 * smug); }
  fr.pooh.armL = .25 + smug * (.6 + Math.sin(t * 8) * .1);
  // s2 crickets: awkward darting glances
  const awk = pulse(t, bs('crickets'), bs('crickets') + .2, be('s2e'), be('s2e') + .6);
  for (const k of ['owl', 'rabbit', 'pooh', 'piglet']) fr[k].smile = lerp(fr[k].smile, .08, awk);
  const sideEye = { pooh: 'rabbit', rabbit: 'owl', owl: 'pooh', piglet: 'pooh' };
  // s2b Pooh changes the subject
  const subj = pulse(t, bs('s2b') - .2, bs('s2b') + .2, be('s2b') + .4, be('s2b') + 1);
  fr.pooh.headTurn = -.8 * subj; fr.pooh.armL = lerp(fr.pooh.armL, 2.7 + Math.sin(t * 9) * .15, subj); fr.pooh.smile = lerp(fr.pooh.smile, .35, subj);
  // s2c Rabbit condescending
  const cond = pulse(t, bs('s2c') - .1, bs('s2c') + .3, be('s2c') + .3, be('s2d'));
  fr.rabbit.lid = Math.max(fr.rabbit.lid, .42 * cond); fr.rabbit.browUp = .5 * cond; fr.rabbit.headTilt = (fr.rabbit.headTilt || 0) + .1 * cond; fr.rabbit.armR = lerp(fr.rabbit.armR, 1.0 + Math.sin(t * 5) * .15, cond);
  fr.rabbit.smile = lerp(fr.rabbit.smile, .15, cond);
  // s2d Owl adjusts spectacles
  const ow = pulse(t, bs('s2d') - .2, bs('s2d') + .3, be('s2d'), be('s2d') + .5);
  fr.owl.wingR = Math.max(fr.owl.wingR, 2.3 * ow); fr.owl.lid = .38 * ow; fr.owl.tilt = -.04 * ow; fr.owl.specSlip = -3 * ow;
  // s2e Piglet anxious
  const anx = pulse(t, bs('s2e') - .2, bs('s2e') + .2, be('s2e') + .2, be('s2e') + .8);
  fr.piglet.tremble = anx; fr.piglet.browIn = anx; fr.piglet.wide = .3 * anx; fr.piglet.armL = lerp(fr.piglet.armL, 1.1, anx); fr.piglet.armR = lerp(fr.piglet.armR, 1.1, anx); fr.piglet.earsDown = .5 * anx;
  // after s2: back to picnic
  const back2pic = pulse(t, bs('s2g'), bs('s2g') + 1, S3.start + 3, S3.start + 4);
  for (const k of ['owl', 'rabbit', 'pooh', 'piglet']) fr[k].smile = lerp(fr[k].smile, .5, back2pic);
  // s3: friends notice Eeyore smiling
  const notice = ramp(t, be('s3c') + .2, be('s3c') + .6) * (1 - ramp(t, bs('s3h') + 1, bs('s3h') + 2));
  for (const k of ['owl', 'rabbit', 'pooh', 'piglet']) { fr[k].wide = Math.max(fr[k].wide || 0, notice * .5); fr[k].smile = lerp(fr[k].smile, -.1, notice); fr[k].browUp = Math.max(fr[k].browUp || 0, notice * .5); }
  fr.piglet.bob -= 26 * pulse(t, be('s3c') + .25, be('s3c') + .4, be('s3c') + .4, be('s3c') + .7);
  const sus = pulse(t, bs('s3d1') - .3, bs('s3d1'), be('s3e'), be('s3e') + .6);
  fr.rabbit.tilt = .1 * sus; fr.rabbit.squint = .7 * sus; fr.rabbit.browAngry = .35 * sus; fr.rabbit.wide = lerp(fr.rabbit.wide, 0, sus); fr.rabbit.clipboard = t > bs('s3d1') - .3 && t < SCENES.s3.end;
  fr.rabbit.armR = lerp(fr.rabbit.armR, .9, ramp(t, bs('s3d1') - .3, bs('s3d1')) * (1 - ramp(t, S3.end - 1, S3.end)));
  const mag = pulse(t, bs('s3e') - .4, bs('s3e'), bs('s3h') + .5, bs('s3h') + 1.2);
  fr.owl.magnify = mag; fr.owl.wide = Math.max(fr.owl.wide, mag * .2);
  const relieved = ramp(t, bs('s3i') - .2, bs('s3i') + .8);
  for (const k of ['owl', 'rabbit', 'pooh', 'piglet']) { fr[k].smile = lerp(fr[k].smile, .6, relieved); fr[k].wide = lerp(fr[k].wide || 0, 0, relieved); fr[k].browUp = lerp(fr[k].browUp || 0, 0, relieved); fr[k].lid = lerp(fr[k].lid || 0, .25, relieved); }
  if (relieved > 0) { fr.rabbit.headTilt = .06 * Math.sin(t * 3) * relieved; fr.pooh.headTilt = .05 * Math.sin(t * 3 + 1) * relieved; }

  for (const k in fr) heads[k] = HEADS[k](fr[k]);
  heads.eeyore = HEADS.eeyore(eSt);
  if (bird) heads.bird = HEADS.bird(bird);

  // ---------- gaze targets
  const eeyTarget = (tt) => {
    if (tt < S1.start) return [ex - 300, 905];                                  // staring at the ground
    if (tt > bs('s3in') && tt < be('s3b') + .5 && bird) return heads.bird;       // looking at the bird
    if (tt > be('s3b') + .5 && tt < bs('s3d1') - .2) return [2600, 450];         // dreaming toward the pasture
    if (tt > bs('s1f') && tt < bs('s1g') + .4) return [ex - 200, 820];          // thinking, eyes low
    if (tt > bs('s2f') && tt < S3.start) return [ex - 260, 960];
    if (tt > bs('s3h') + 1) return [ex - 300, 960];
    return talkTarget('eeyore', heads, heads.pooh)(tt);
  };
  const friendTarget = (name) => (tt) => {
    if (tt < S1.start) return name === 'owl' ? heads.rabbit : heads.owl;
    if (tt >= bs('crickets') && tt < bs('s2b')) {
      const ph = Math.floor((tt - bs('crickets')) / .45 + hashStr(name) % 3) % 3;
      return ph === 1 ? heads[sideEye[name]] : heads.eeyore;
    }
    if (name === 'pooh' && tt >= bs('s2b') && tt < be('s2b') + .3) return [700 + Math.sin(tt * 4) * 300, 760];
    if (tt > bs('s2g') && tt < be('s3c') + .2) return name === 'pooh' ? heads.piglet : heads.pooh;
    if (tt > be('s3c') + .2 && tt < bs('s3i')) return heads.eeyore;
    return talkTarget(name, heads, heads.eeyore)(tt);
  };

  // ---------- draw
  drawClearing(c, cam, { t });
  c.save(); applyCam(c, cam);
  const order = ['owl', 'rabbit', 'pooh', 'piglet'];
  for (const k of order) {
    const st = mk(k, t, fr[k], friendTarget(k));
    if (fr[k].mouthAuto && !lineAt(t)) st.mouth = Math.max(0, Math.sin(t * 9)) * .4 * fr[k].mouthAuto;
    DRAW[k](c, st);
  }
  if (t > SCENES.s1.start - .1 && t < bs('s1e')) drawHoneyPot(c, 1110, 905, .8);
  drawHoneyPot(c, 880, 935, .7);
  const eS = mk('eeyore', t, eSt, eeyTarget);
  if (eWalk > 0 && eWalk < 1) eS.walk = 1;
  if (t > bs('s3f') - .3 && t < be('s3g') + .3) eS.blink = 0;
  drawEeyore(c, eS);
  if (bird) drawBird(c, mk('bird', t, bird, (tt) => heads.eeyore));
  // thought bubbles
  const hp = HEADS.eeyore(eSt);
  const tb = pulse(t, bs('s1f') - .2, bs('s1f') + .3, be('s1g') + .1, be('s1g') + .5);
  if (tb > 0) {
    const bx = hp[0] - 40, by = hp[1] - 190;
    thoughtBubble(c, bx, by, 230 * (.6 + .4 * tb), 150 * (.6 + .4 * tb), tb, [hp[0] + 10, hp[1] - 50]);
    c.save(); c.globalAlpha = tb; c.fillStyle = '#4a3424'; c.font = '600 84px Fredoka'; c.textAlign = 'center'; c.textBaseline = 'middle';
    if (t < bs('s1g')) c.fillText('?', bx, by + 4);
    else { drawHoneyPot(c, bx - 30, by + 40, .6); c.fillText('?', bx + 50, by + 4); }
    c.restore();
  }
  const pa = pulse(t, bs('s2a') + .3, bs('s2a') + 1.1, bs('s2g') + .6, bs('s2g') + 1.2);
  if (pa > 0) {
    const pop = 1 - ramp(t, bs('s2f') + 1, bs('s2g') + .9, easeIn);
    const sc = Math.max(.02, pop * (t < bs('s2a') + 1.1 ? back(prog(t, bs('s2a') + .3, bs('s2a') + 1.1)) : 1));
    const bx = hp[0] - 60, by = hp[1] - 240;
    thoughtBubble(c, bx, by, 380 * sc, 250 * sc, Math.min(1, pa * 1.5), [hp[0] + 10, hp[1] - 50]);
    miniPasture(c, bx, by, 380 * sc, 250 * sc, t, Math.min(1, pa * 1.5));
    if (sc < .12 && t > bs('s2g')) { c.strokeStyle = OUT; c.lineWidth = 4; for (let i = 0; i < 8; i++) { const a = i * TAU / 8, r = 30 + prog(t, bs('s2g') + .7, bs('s2g') + 1.2) * 40; c.beginPath(); c.moveTo(bx + Math.cos(a) * r, by + Math.sin(a) * r); c.lineTo(bx + Math.cos(a) * (r + 18), by + Math.sin(a) * (r + 18)); c.stroke(); } }
  }
  c.restore();
  // warm light when Eeyore is hopeful
  c.save(); applyCam(c, cam, 1);
  c.restore();
  sunbeam(c, 1500 + (cam.x - 1300) * -.3, joy * .9, t);
  finish(c, { vignette: .45 + .25 * ramp(t, bs('s1f') - .3, bs('s1f')) * (1 - ramp(t, be('s1g'), be('s1g') + .5)) });
  // title
  const ta = Math.min(ramp(t, .2, 1.1), 1 - ramp(t, 2.6, 3.3));
  if (ta > 0) {
    c.save(); c.globalAlpha = ta; c.textAlign = 'center';
    c.font = '600 112px Fredoka'; c.lineWidth = 12; c.strokeStyle = 'rgba(61,43,31,.85)'; c.lineJoin = 'round';
    c.strokeText('Eeyore & the Pasture', W / 2, 330 + (1 - ta) * 20); c.fillStyle = '#fff6df'; c.fillText('Eeyore & the Pasture', W / 2, 330 + (1 - ta) * 20);
    c.font = '50px "Patrick Hand"'; c.lineWidth = 8; c.strokeText('a story about emotional needs', W / 2, 410); c.fillText('a story about emotional needs', W / 2, 410);
    c.restore();
  }
  fadeBlack(c, 1 - ramp(t, 0, .8));
}

// ---------------------------------------------------------------- S4 forest edge / misaligned needs
function sceneEdge(c, t) {
  const S = SCENES.s4;
  const cam = kf(t, [
    [S.start, { x: 1350, y: 560, z: .64 }], [bs('s4a') + .5, { x: 1250, y: 580, z: .66 }], [bs('s4a') + 2, { x: 330, y: 760, z: 1.12 }],
    [be('s4a'), { x: 360, y: 760, z: 1.12 }], [bs('s4b') + 1.5, { x: 1900, y: 620, z: .85 }], [be('s4b'), { x: 2000, y: 620, z: .85 }],
    [bs('s4c') + .8, { x: 1120, y: 760, z: 1.35 }], [bs('s4d') + .5, { x: 980, y: 720, z: .95 }], [S.end, { x: 1000, y: 720, z: .98 }],
  ]);
  const close = ramp(t, bs('s4c'), be('s4c')) * (1 - ramp(t, be('s4d') - 1, S.end));
  drawEdge(c, cam, { t, close });
  c.save(); applyCam(c, cam);
  // friends with routines
  const heads = {};
  const P = { x: 330, y: 1000, s: .85, honey: true, armR: .9 + Math.max(0, Math.sin(t * 2)) * .6, smile: .7, lid: .2 };
  const Rb = { x: 80, y: 1000, s: .85, clipboard: true, armR: .9, smile: .5, headTilt: Math.sin(t * 2) * .04 };
  const O = { x: -170, y: 990, s: .85, wingR: .9, wingL: .9, smile: .4, lid: .3, gy: .8 };
  const Pg = { x: 560, y: 1010, s: .8, smile: .5, armR: .6 + Math.sin(t * 6) * .4, bob: -Math.abs(Math.sin(t * 6)) * 4 };
  heads.pooh = HEADS.pooh(P);
  const eT = turns(t, 1, [bf('s4d', .1), bf('s4d', .45)]);
  const E = { x: 1050, y: 1010, s: .9, ...eT, ears: .15, headDrop: .6, lid: .4, browIn: .8, smile: -.3 };
  E.ears += .4 * pulse(t, bs('s4b'), bs('s4b') + 1.5, be('s4b'), bs('s4c') + .5);
  E.lid -= .3 * pulse(t, bs('s4b'), bs('s4b') + 1.5, be('s4b'), bs('s4c') + .5);
  E.headDrop -= .3 * pulse(t, bs('s4b'), bs('s4b') + 1.5, be('s4b'), bs('s4c') + .5);
  E.desat = .3 * close; E.ears -= .15 * close;
  E.ears += .35 * pulse(t, bf('s4d', .5), bf('s4d', .6), bf('s4d', .72), bf('s4d', .82));
  const eyeT = (tt) => {
    if (tt > be('s4c') && tt < bs('s4d')) return Math.floor((tt - be('s4c')) / .45) % 2 ? [300, 800] : [2500, 700];
    if (tt > bf('s4d', .1) && tt < bf('s4d', .45)) return heads.pooh;
    if (tt > bf('s4d', .78)) return heads.pooh;
    return [2600, 650];
  };
  // book for owl
  DRAW.owl(c, mk('owl', t, O, null));
  c.save(); c.translate(-170, 990 - 115); c.fillStyle = '#f7f0dc'; c.strokeStyle = OUT; c.lineWidth = 3;
  c.beginPath(); c.moveTo(0, 0); c.lineTo(-55, -10); c.lineTo(-55, 40); c.lineTo(0, 50); c.lineTo(55, 40); c.lineTo(55, -10); c.closePath(); c.fill(); c.stroke();
  c.beginPath(); c.moveTo(0, 0); c.lineTo(0, 50); c.stroke(); c.restore();
  DRAW.rabbit(c, mk('rabbit', t, Rb, null));
  DRAW.pooh(c, mk('pooh', t, P, () => heads.pooh.map((v, i) => v + (i ? 80 : 120))));
  DRAW.piglet(c, mk('piglet', t, Pg, () => heads.pooh));
  // broom
  c.save(); c.translate(560 + 30, 1010 - 90); c.rotate(.5 + Math.sin(t * 6) * .25); c.strokeStyle = '#7a5532'; c.lineWidth = 6; c.beginPath(); c.moveTo(0, 0); c.lineTo(0, 95); c.stroke();
  c.fillStyle = '#d9b46a'; c.beginPath(); c.moveTo(-14, 95); c.lineTo(14, 95); c.lineTo(20, 125); c.lineTo(-20, 125); c.closePath(); c.fill(); c.lineWidth = 3; c.strokeStyle = OUT; c.stroke(); c.restore();
  drawEeyore(c, mk('eeyore', t, E, eyeT));
  butterflies(c, t, 2300, 760, 5, 600);
  c.restore();
  finish(c, { vignette: .45 + .4 * close });
}

// ---------------------------------------------------------------- S5 the toxic cycle
const CYCLE = [
  ['s5b', 'Stays in the forest to keep the peace'],
  ['s5c', 'Needs go unmet. He gets sadder.'],
  ['s5d', 'Friends offer surface-level fixes'],
  ['s5e', 'Feels more misunderstood & isolated'],
  ['s5f', 'The cycle repeats'],
];
function sceneCycle(c, t) {
  const S = SCENES.s5;
  const cx = 960, cy = 520, Rr = 320, RX = 520;
  const steps = CYCLE.map(([l]) => ramp(t, bs(l) - .2, bs(l) + .4));
  const sad = steps.reduce((a, b) => a + b, 0) / 5;
  drawParchment(c, sad * .35);
  const node = (i) => { const a = -Math.PI / 2 + i * TAU / 5; return [cx + Math.cos(a) * RX, cy + Math.sin(a) * Rr]; };
  // arcs
  c.lineCap = 'round';
  for (let i = 0; i < 5; i++) {
    const k = i < 4 ? ramp(t, bs(CYCLE[i + 1][0]) - .3, bs(CYCLE[i + 1][0]) + .3) : ramp(t, bs('s5f') + .2, bs('s5f') + .8);
    if (k <= 0) continue;
    const a0 = -Math.PI / 2 + i * TAU / 5 + .22, a1 = a0 + (TAU / 5 - .44) * k;
    c.strokeStyle = 'rgba(74,52,36,.75)'; c.lineWidth = 7; c.setLineDash([]);
    c.beginPath(); c.ellipse(cx, cy, RX, Rr, 0, a0, a1); c.stroke();
    const hx = cx + Math.cos(a1) * RX, hy = cy + Math.sin(a1) * Rr, ang = Math.atan2(Math.cos(a1) * Rr, -Math.sin(a1) * RX);
    c.save(); c.translate(hx, hy); c.rotate(ang); c.fillStyle = 'rgba(74,52,36,.9)'; c.beginPath(); c.moveTo(12, 0); c.lineTo(-10, -11); c.lineTo(-10, 11); c.closePath(); c.fill(); c.restore();
  }
  // racing dot during "repeats"
  const spin = prog(t, bs('s5f') + .3, S.end - .3);
  if (spin > 0 && spin < 1) {
    const a = -Math.PI / 2 + easeIn(spin) * TAU * 3;
    c.fillStyle = '#c0392b'; c.beginPath(); c.arc(cx + Math.cos(a) * RX, cy + Math.sin(a) * Rr, 14, 0, TAU); c.fill();
  }
  // cards
  c.font = '40px "Patrick Hand"'; c.textAlign = 'center'; c.textBaseline = 'middle';
  CYCLE.forEach(([l, txt], i) => {
    const k = steps[i]; if (k <= 0) return;
    const [x, y] = node(i); const w = c.measureText(txt).width + 80;
    const hl = pulse(t, bs(l), bs(l) + .3, be(l), be(l) + .4) + (spin > 0 ? .5 * Math.max(0, Math.cos((easeIn(spin) * 15 - i) * TAU / 5 * 1.0)) : 0);
    c.save(); c.translate(x, y); c.scale(back(k) * (1 + .04 * hl), back(k) * (1 + .04 * hl)); c.globalAlpha = clamp(k * 2);
    c.fillStyle = hl > .3 ? '#fff4d6' : '#fbf6ea'; roundRect(c, -w / 2, -40, w, 80, 18); c.fill(); c.strokeStyle = OUT; c.lineWidth = 3.5; c.stroke();
    c.fillStyle = '#c0632b'; c.beginPath(); c.arc(-w / 2, -40, 26, 0, TAU); c.fill(); c.stroke();
    c.fillStyle = '#fff'; c.font = '600 30px Fredoka'; c.fillText(String(i + 1), -w / 2, -38);
    c.fillStyle = '#3d2b1f'; c.font = '40px "Patrick Hand"'; c.fillText(txt, 0, 2);
    c.restore();
  });
  // Eeyore in the centre, getting greyer
  const E = mk('eeyore', t, { x: cx - 70, y: cy + 170, s: .55, facing: 1, ears: .1 - sad * .15, headDrop: .75 + sad * .25, lid: .45 + sad * .2, browIn: .9, smile: -.35 - sad * .3, desat: sad * .55, sag: sad * 6 }, () => [cx + 400, cy + 400]);
  if (spin > 0) E.blink = 0;
  drawEeyore(c, E);
  rainCloud(c, cx + 20, cy - 60 - sad * 10, .9 + sad * .5, .3 + sad * .7, ramp(t, bs('s5c'), be('s5c')), t);
  // Pooh pops in with honey
  const pp = pulse(t, bs('s5d') - .4, bs('s5d'), be('s5d') + .4, be('s5d') + .9);
  if (pp > 0) {
    c.save(); c.globalAlpha = clamp(pp * 2);
    drawPooh(c, mk('pooh', t, { x: cx + 330, y: cy + 250 + (1 - back(pp)) * 60, s: .5, honey: true, armR: 1.4, smile: .8 }, () => [cx, cy + 100]));
    c.restore();
  }
  finish(c, { vignette: .35 + sad * .3 });
  fadeBlack(c, 1 - ramp(t, S.start, S.start + .5));
}

// ---------------------------------------------------------------- S6 storm / breaking point,  S7 hard truth, S8 takeaway (part 1)
function sceneStorm(c, t) {
  const S6 = SCENES.s6, S7 = SCENES.s7, S8 = SCENES.s8;
  const inS6 = t < S7.start;
  const shout = bs('s6b'), crack = bf('s6b', .86);
  const stormAmt = inS6 ? (t < be('s6b') + .1 ? 1 : lerp(1, .25, ramp(t, be('s6b') + .1, be('s6b') + .8))) : 0;
  const golden = inS6 ? 0 : 1;
  const cam = kf(t, [
    [S6.start, { x: 1180, y: 620, z: 1.2 }], [bs('s6a') + .5, { x: 1260, y: 630, z: 1.35 }],
    [shout - .15, { x: 1300, y: 630, z: 1.4 }], [shout + .1, { x: 1380, y: 620, z: 1.95 }], [be('s6b') + .3, { x: 1380, y: 620, z: 1.95 }],
    [be('s6b') + 1.4, { x: 1150, y: 610, z: 1.12 }], [bs('s6d'), { x: 1180, y: 620, z: 1.15 }], [S6.end, { x: 1430, y: 640, z: 1.45 }],
    [S7.start, { x: 1320, y: 650, z: 1.75 }], [be('s7a') + 1, { x: 1320, y: 650, z: 1.8 }], [bs('s7b') + 2.5, { x: 1150, y: 615, z: 1.08 }],
    [S7.end, { x: 1250, y: 620, z: 1.2 }], [S8.start, { x: 1320, y: 650, z: 1.6 }], [be('s8b'), { x: 1330, y: 650, z: 1.65 }],
    [be('s8b') + 2.5, { x: 1500, y: 620, z: 1.2 }],
  ]);
  if (t > crack && t < crack + .6) { const k = 1 - prog(t, crack, crack + .6); cam.x += Math.sin(t * 95) * 12 * k; cam.y += Math.cos(t * 81) * 9 * k; }
  drawClearing(c, cam, { t, storm: stormAmt, golden });
  // long forest shadows on the ground (s7b "holding him back")
  const bars = inS6 ? 0 : pulse(t, bs('s7b') + .5, bs('s7b') + 2, be('s7c') - 1, be('s7c'));
  c.save(); applyCam(c, cam);
  if (bars > 0) {
    c.fillStyle = `rgba(40,30,50,${.28 * bars})`;
    for (let i = 0; i < 9; i++) { const x = 300 + i * 190; c.beginPath(); c.moveTo(x, 720); c.lineTo(x + 50, 720); c.lineTo(x + 330, 1150); c.lineTo(x + 230, 1150); c.fill(); }
  }
  const heads = {};
  // Pooh
  const P = { x: 1130, y: 905, s: .85, smile: .45 };
  const offer = inS6 ? pulse(t, bs('s6a') - .3, bs('s6a') + .3, be('s6b') + .3, be('s6b') + .5) : 0;
  P.armR = .3 + 1.2 * offer; P.honey = inS6 && t < be('s6b') + .3; if (inS6) P.armL = 2.65;
  const stun = inS6 ? ramp(t, be('s6b') - .2, be('s6b') + .2) : 0;
  P.wide = stun * (1 - ramp(t, bs('s6d'), be('s6d'))) * .8; P.browUp = P.wide; P.smile = lerp(P.smile, -.1, stun);
  if (inS6 && t > be('s6b') - .2) P.mouth = 0;
  // S7 Pooh sad
  if (!inS6) {
    P.browIn = .9; P.smile = -.2; P.tearShine = 1; P.lid = .2;
    P.tear = clamp(prog(t, bs('s7a') + .3, bs('s7a') + 2.4));
    P.armR = .3 + 1.0 * pulse(t, bs('s7a') - .2, bs('s7a') + .4, bs('s7b') + 1, bs('s7b') + 2);
    if (t > S8.start) { P.browIn = .7; P.smile = .05 + .25 * ramp(t, be('s8a'), be('s8b')); P.headTilt = .1 * Math.sin(prog(t, be('s8a') + .2, be('s8a') + 1.5) * TAU * 1.5) * (1 - ramp(t, be('s8a') + 1.4, be('s8a') + 1.6)); }
    const wv = pulse(t, be('s8b') + 1.5, be('s8b') + 1.8, be('s8b') + 4, be('s8b') + 4.5);
    if (wv > 0) P.armR = lerp(P.armR, 2.3 + Math.sin(t * 7) * .2, wv);
  }
  heads.pooh = HEADS.pooh(P);
  // Eeyore
  const turnsE = inS6 ? [] : [bf('s7c', .45), S8.start + .1, be('s8b') - .2];
  const eT = turns(t, -1, turnsE.filter(x => x));
  const E = { x: 1480, y: 905, s: .85, ...eT, ears: .0, headDrop: .95, lid: .58, browIn: .95, smile: -.5, mouthK: .9 };
  if (inS6) {
    const lift = ramp(t, be('s6a') + .1, shout + .2);
    E.headDrop = lerp(.95, .35, lift); E.lid = lerp(.58, .1, lift); E.ears = lerp(0, .3, lift);
    const yell = pulse(t, shout - .1, shout + .2, be('s6b'), be('s6b') + 1.2);
    E.ears = lerp(E.ears, .95, yell); E.wide = .55 * yell; E.browIn = lerp(E.browIn, .75, yell); E.headDrop = lerp(E.headDrop, .15, yell); E.mouthK = 1.35;
    E.tremble = lift;
    const calm = ramp(t, be('s6b') + .8, bs('s6d'));
    E.ears = lerp(E.ears, .55, calm); E.headDrop = lerp(E.headDrop, .25, calm); E.lid = lerp(E.lid, .12, calm); E.browIn = lerp(E.browIn, .25, calm); E.smile = lerp(E.smile, -.05, calm);
    E.sag = Math.sin(t * 5) * 4 * pulse(t, be('s6b'), be('s6b') + .2, bs('s6c') + 1, bs('s6c') + 3);
  } else {
    Object.assign(E, { ears: .35, headDrop: .4, lid: .2, browIn: .55, smile: -.1 });
    const toLight = ramp(t, bf('s7c', .4), bf('s7c', .7));
    E.ears = lerp(E.ears, .7, toLight); E.lid = lerp(E.lid, .08, toLight); E.headDrop = lerp(E.headDrop, .2, toLight); E.browIn = lerp(E.browIn, .3, toLight);
    if (t > S8.start) Object.assign(E, { ears: .45, headDrop: .4, lid: .2, browIn: .5, smile: .25 });
    const go = ramp(t, be('s8b') - .3, be('s8b') + .5);
    E.ears = lerp(E.ears, .8, go); E.headDrop = lerp(E.headDrop, .15, go); E.smile = lerp(E.smile, .45, go); E.lid = lerp(E.lid, .05, go);
    const wk = prog(t, be('s8b') + .3, be('s8b') + 3.2);
    E.x = lerp(1480, 2350, wk); if (wk > 0 && wk < 1) { E.walk = 1; E.phase = t * 1.7; }
  }
  heads.eeyore = HEADS.eeyore(E);
  const eTarget = (tt) => {
    if (inS6 && tt < be('s6a') + .3) return [E.x - 200, 1000];
    if (!inS6 && tt > bf('s7c', .4) && tt < S8.start) return [2800, 500];
    if (!inS6 && tt > bs('s8b') + .3) return [2800, 600];
    return heads.pooh;
  };
  // friends sheltering under the oak (storm) / watching
  const others = inS6 ? [
    ['owl', { x: 300, y: 905, s: .8, smile: .1, browIn: .4 }], ['rabbit', { x: 470, y: 905, s: .8, smile: .1, browIn: .4, armL: .9, armR: .9 }],
    ['piglet', { x: 620, y: 905, s: .75, smile: 0, browIn: .7, tremble: .6, earsDown: .7 }],
  ] : [
    ['owl', { x: 560, y: 905, s: .8, smile: .1, browIn: .5, lid: .2 }], ['rabbit', { x: 740, y: 905, s: .8, smile: .05, browIn: .5, armL: .5, armR: .5 }],
    ['piglet', { x: 900, y: 905, s: .75, smile: .05, browIn: .8, lid: .1 }],
  ];
  for (const [k, st] of others) {
    if (inS6) { st.wide = stun * .7; st.browUp = stun * .6; st.specSlip = stun * 10; }
    DRAW[k](c, mk(k, t, st, () => heads.eeyore));
  }
  if (inS6) drawUmbrella(c, 1035, 905 - 395, .95, -.05);
  DRAW.pooh(c, mk('pooh', t, P, () => heads.eeyore));
  // dropped honey pot
  if (inS6 && t > be('s6b') + .3) {
    const k = prog(t, be('s6b') + .3, be('s6b') + .7);
    c.save(); c.translate(1230, lerp(780, 920, easeIn(k))); c.rotate(k * 1.3); drawHoneyPot(c, 0, 0, .75); c.restore();
  }
  drawEeyore(c, mk('eeyore', t, E, eTarget));
  if (inS6) rainCloud(c, E.x + 20, 905 - 410 - (1 - stormAmt) * 200, 1.3, 1, stormAmt, t);
  c.restore();
  rain(c, t, stormAmt * (inS6 ? 1 : 0));
  // light: lightning flash, sunbeam after shout, golden warm light from the right in s7
  if (inS6 && t > crack && t < crack + .35) fadeBlack(c, .75 * (1 - prog(t, crack, crack + .35)), '255,255,255');
  if (inS6 && t > 145.7 - 145.38 + S6.start && t < S6.start + .6) fadeBlack(c, .4 * (1 - prog(t, S6.start + .3, S6.start + .6)), '255,255,255');
  sunbeam(c, 1650 + (1300 - cam.x) * .3, inS6 ? ramp(t, be('s6b') + .6, be('s6b') + 2.2) : ramp(t, bf('s7c', .3), bf('s7c', .8)), t);
  if (!inS6) { const g = c.createLinearGradient(W, 0, W * .5, 0); g.addColorStop(0, 'rgba(255,214,140,.28)'); g.addColorStop(1, 'rgba(255,214,140,0)'); c.fillStyle = g; c.fillRect(0, 0, W, H); }
  finish(c, { vignette: inS6 ? .6 : .45 });
  fadeBlack(c, Math.max(1 - ramp(t, S6.start, S6.start + .6), inS6 ? ramp(t, S6.end - .5, S6.end) * 0 : 0));
  fadeBlack(c, ramp(t, be('s8b') + 2.6, be('s8b') + 3.1), '255,250,235');
}

// ---------------------------------------------------------------- S8 part 2: into the pasture
function scenePasture(c, t) {
  const S8 = SCENES.s8;
  const t0 = be('s8b') + 3.1;          // dissolve finished
  const runStart = t0 + 1.2;
  const fr = bs('s8d'), frEnd = be('s8d') + .15;   // cut to friends watching
  // Eeyore x: walks to edge, then gallops, then slows on the hill
  const tRun = Math.max(0, t - runStart);
  const stopT = bs('s8e') + .5, stopX = (() => { const tr = stopT - runStart; return 1250 + 520 * tr - 0; })();
  let ex, walk = 0, gallop = 0, phase = 0;
  if (t < runStart) { ex = lerp(900, 1250, prog(t, t0 - .4, runStart)); walk = 1; phase = t * 1.7; }
  else if (t < stopT) { const accel = Math.min(1, tRun / 1.2); ex = 1250 + 520 * (tRun - (tRun < 1.2 ? 0.6 * (1.2 - tRun) * (1 - accel) : 0)); gallop = Math.min(1, tRun / .5); phase = tRun * 2.3; }
  else { const k = prog(t, stopT, stopT + 1.6); ex = stopX + 520 * 1.6 * (k - k * k / 2) * 1; gallop = 1 - k; walk = k < 1 ? k : 0; phase = (stopT - runStart) * 2.3 + (t - stopT) * 2.3 * (1 - k * .5); }
  const leap = Math.max(0, Math.sin(prog(t, bs('s8c') + 2.3, bs('s8c') + 3.2) * Math.PI)) + Math.max(0, Math.sin(prog(t, bs('s8c') + 4.4, bs('s8c') + 5.3) * Math.PI));
  const ey = 1010 - leap * 110;
  const cam = (t < fr || t > frEnd) ? (t < stopT ? { x: Math.max(1100, ex + 260), y: 660, z: 1.0 } :
    kf(t, [[frEnd, { x: stopX + 300, y: 660, z: 1.0 }], [bs('s8e') + 2, { x: stopX + 520 * .8 + 180, y: 700, z: 1.25 }], [bs('s8f') + 1, { x: stopX + 520 * .8 + 180, y: 700, z: 1.25 }], [be('s8f') + 1, { x: stopX + 520 * .8 + 200, y: 560, z: .72 }]]))
    : { x: 1080, y: 760, z: 1.15 };
  drawEdge(c, cam, { t });
  c.save(); applyCam(c, cam);
  if (t >= fr && t <= frEnd) {
    // friends at the forest edge watching him go
    const dist = { x: 1800 + (t - fr) * 60, y: 800, s: .22, facing: 1, gallop: 1, phase: t * 2.3, ears: 1, headDrop: .1, smile: .9, lid: 0, t, earFlap: 1 };
    drawEeyore(c, dist);
    const target = () => [dist.x, dist.y - 60];
    DRAW.owl(c, mk('owl', t, { x: 700, y: 1000, s: .85, smile: .15, browIn: .4, tilt: .06 }, target));
    DRAW.rabbit(c, mk('rabbit', t, { x: 870, y: 1005, s: .85, smile: .1, browIn: .5, browUp: .3, armL: -.5, armR: -.5 }, target));
    DRAW.pooh(c, mk('pooh', t, { x: 1050, y: 1010, s: .9, smile: .3, browIn: .6, tearShine: .7, armR: 2.2 + Math.sin(t * 6) * .25 }, target));
    DRAW.piglet(c, mk('piglet', t, { x: 1230, y: 1015, s: .8, smile: .45, browIn: .3, armR: 2.2 + Math.sin(t * 9) * .3 }, target));
  } else {
    const joyful = t > runStart;
    const st = {
      x: ex, y: ey, s: .95, facing: 1, walk, gallop, phase, ears: joyful ? .95 : .75, headDrop: joyful ? .1 : .2, lid: 0, smile: joyful ? .95 : .5,
      mouth: 0, earFlap: gallop, tailUp: gallop * .3, sparkle: 1, browIn: 0, mouthK: 1,
    };
    if (joyful && t < stopT) st.mouth = .3 + Math.sin(t * 3) * .05;
    const k = prog(t, stopT + 1.5, stopT + 2.2);
    if (k > 0) { st.lid = .55 * k * (1 - pulse(t, bs('s8f') + 1, bs('s8f') + 1.3, bs('s8f') + 4, bs('s8f') + 4.3)); st.smile = .9; st.headDrop = .05; st.headTilt = -.1 * k; st.tailWag = 1; }
    drawEeyore(c, mk('eeyore', t, st, () => [ex + 900, 600 - leap * 100]));
    butterflies(c, t, ex + 300, 700, 5, 500);
  }
  c.restore();
  sunbeam(c, 1500, .6, t);
  finish(c, { vignette: .35 });
  fadeBlack(c, 1 - ramp(t, t0 - .4, t0 + .4), '255,250,235');
  // end card
  const ea = ramp(t, bs('end') + .3, bs('end') + 1.6);
  if (ea > 0) {
    c.save(); c.fillStyle = `rgba(40,28,18,${.45 * ea})`; c.fillRect(0, 0, W, H); c.globalAlpha = ea; c.textAlign = 'center';
    c.font = '600 92px Fredoka'; c.lineWidth = 10; c.strokeStyle = 'rgba(61,43,31,.9)'; c.lineJoin = 'round';
    c.strokeText('Some of us need pastures.', W / 2, H / 2 - 10); c.fillStyle = '#fff6df'; c.fillText('Some of us need pastures.', W / 2, H / 2 - 10);
    c.font = '48px "Patrick Hand"'; c.lineWidth = 7; const sub = "This isn't working for me, and that's okay.";
    c.globalAlpha = ramp(t, bs('end') + 1.5, bs('end') + 2.6); c.strokeText(sub, W / 2, H / 2 + 80); c.fillText(sub, W / 2, H / 2 + 80);
    c.restore();
  }
  fadeBlack(c, ramp(t, TL.duration - 1.4, TL.duration - .1));
}

// ---------------------------------------------------------------- dispatcher
window.renderAt = function (t) {
  begin();
  const c = ctx;
  c.save();
  if (t < SCENES.s4.start) sceneClearing(c, t);
  else if (t < SCENES.s5.start) sceneEdge(c, t);
  else if (t < SCENES.s6.start) sceneCycle(c, t);
  else if (t < be('s8b') + 3.1) sceneStorm(c, t);
  else scenePasture(c, t);
  c.restore();
  // cross-dissolves between big scene changes
  for (const id of ['s4', 's5', 's6']) { const s = SCENES[id].start; if (t >= s && t < s + .5) fadeBlack(c, 1 - prog(t, s, s + .5)); if (t < s && t > s - .5) fadeBlack(c, prog(t, s - .5, s)); }
  chapterLayer(c, t);
  captionLayer(c, t);
};
