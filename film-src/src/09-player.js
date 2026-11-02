// ============================================================================
//  PLAYER — clock, scheduler, seeking, captions, HUD, post-processing, loop
// ============================================================================
(() => {
  if (/render/.test(location.hash)) return;   // video export drives the film itself (see RENDER)
  const cv = document.getElementById('stage');
  const ctx = cv.getContext('2d', { alpha: false });
  const $ = s => document.querySelector(s);
  const intro = $('#intro'), hud = $('#hud'), endCard = $('#end');
  const capBox = $('#captions'), chapLabel = $('#chap-label'), track = $('#track'), fill = $('#fill');
  const btnPlay = $('#btn-play'), btnMute = $('#btn-mute'), btnFull = $('#btn-full'), btnBegin = $('#btn-begin'), btnAgain = $('#btn-again');
  const lbT = $('#lb-top'), lbB = $('#lb-bot');
  const reduceMotion = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  const DUR = Film.duration;
  let W = 0, H = 0, DPR = 1, dprCap = Math.min(window.devicePixelRatio || 1, 2);

  function resize() {
    W = window.innerWidth; H = window.innerHeight;
    DPR = Math.max(0.5, Math.min(dprCap, Math.sqrt(3.6e6 / Math.max(1, W * H))));
    dirty = true;
    cv.width = Math.max(1, Math.round(W * DPR)); cv.height = Math.max(1, Math.round(H * DPR));
    cv.style.width = W + 'px'; cv.style.height = H + 'px';
    Film.resize && Film.resize(W, H, DPR);
  }
  window.addEventListener('resize', resize);

  // ---------- clock
  const P = { t: 0, playing: false, started: false, ended: false, aT: 0, aA: 0, aP: 0 };
  let lastNow = 0, dirty = true, lastDrawT = NaN;
  const now = () => {
    if (!Sound.ok) return performance.now() / 1000;
    const ac = Sound.ctx; let v;
    const o = ac.getOutputTimestamp && ac.getOutputTimestamp();
    if (o && o.contextTime > 0 && o.performanceTime > 0) v = o.contextTime + Math.min(0.1, (performance.now() - o.performanceTime) / 1000);
    else v = ac.currentTime - (ac.outputLatency || ac.baseLatency || 0);
    return (lastNow = Math.max(lastNow, v));
  };
  function clockT() { return P.playing ? Math.min(DUR, P.aT + (now() - P.aA)) : P.t; }

  // ---------- scheduler
  const EV = Film.events.slice().sort((a, b) => a.t - b.t);
  let ptr = 0;
  const lowerBound = t => { let lo = 0, hi = EV.length; while (lo < hi) { const m = (lo + hi) >> 1; if (EV[m].t < t) lo = m + 1; else hi = m; } return lo; };
  function schedule(t) {
    if (!Sound.ok) return;
    const horizon = t + 0.35;
    while (ptr < EV.length && EV[ptr].t <= horizon) {
      const ev = EV[ptr++];
      if (ev.t < t - 0.15) continue;           // missed, skip
      Sound.play(ev, Math.max(Sound.time + 0.005, P.aA + (ev.t - P.aT)));
    }
  }
  function seek(t, resumeSustains = true) {
    t = clamp(t, 0, DUR);
    lastNow = 0; dirty = true;
    P.t = t; P.aT = t; P.aA = now();
    P.ended = false; endCard.hidden = true;
    if (Sound.ok) {
      Sound.newEpoch();
      ptr = lowerBound(t);
      if (resumeSustains && P.playing) {
        for (let i = 0; i < ptr; i++) {
          const ev = EV[i];
          if (ev.len && ev.t + ev.len > t + 0.6) Sound.play(ev, Sound.time + 0.02, t - ev.t);
        }
      }
    }
    Film.seek && Film.seek(t);
  }

  // ---------- transport
  async function play() {
    if (P.ended) seek(0);
    await Sound.resume();
    P.aT = P.t; P.aA = now(); P.playing = true;
    if (!P.started) { P.started = true; }
    else seek(P.t);
    btnPlay.setAttribute('aria-label', 'Pause'); btnPlay.dataset.state = 'playing';
    requestWake();
  }
  async function pause() {
    P.t = clockT(); P.playing = false; dirty = true;
    releaseWake();
    await Sound.suspend();
    btnPlay.setAttribute('aria-label', 'Play'); btnPlay.dataset.state = 'paused';
    showHud();
  }
  const toggle = () => P.playing ? pause() : play();

  // ---------- wake lock
  let wake = null;
  function releaseWake() { try { wake && wake.release(); } catch (e) { } wake = null; }
  async function requestWake() { try { if ('wakeLock' in navigator && !wake) { wake = await navigator.wakeLock.request('screen'); wake.addEventListener('release', () => wake = null); } } catch (e) { wake = null; } }

  // ---------- captions
  const LINES = Film.narration.map((n, idx) => {
    const p = document.createElement('p');
    p.className = 'cap' + (n.cls ? ' ' + n.cls : '');
    // " / " marks a line break; words fade in one after another
    const spans = [];
    n.text.split(' / ').forEach((line, li) => {
      if (li) p.appendChild(document.createElement('br'));
      const words = line.trim().split(/\s+/);
      words.forEach((w, i) => {
        const s = document.createElement('span'); s.textContent = w; s.className = 'w';
        p.appendChild(s); if (i < words.length - 1) p.appendChild(document.createTextNode(' '));
        spans.push(s);
      });
    });
    p.style.display = 'none';
    capBox.appendChild(p);
    const hold = n.d ?? Math.max(3, 2.5 + n.text.replace(/ \/ /g, ' ').length * 0.06);
    return { ...n, el: p, spans, d: hold, on: false };
  });
  function updateCaptions(t) {
    for (const L of LINES) {
      const lt = t - L.t;
      const vis = lt > -0.05 && lt < L.d;
      if (vis !== L.on) { L.el.style.display = vis ? '' : 'none'; L.on = vis; }
      if (!vis) continue;
      const out = clamp((L.d - lt) / 0.9);
      const stagger = Math.min(0.11, 1.4 / L.spans.length);
      for (let i = 0; i < L.spans.length; i++) {
        // with narration, each word surfaces just ahead of the voice speaking it
        const k = (L.w ? smooth((lt - L.w[i] + 0.12) / 0.45) : smooth((lt - i * stagger) / 0.7)) * out;
        const s = L.spans[i];
        s.style.opacity = k.toFixed(3);
        s.style.transform = `translateY(${((1 - k) * 0.28).toFixed(3)}em)`;
        s.style.filter = reduceMotion ? '' : `blur(${((1 - k) * 4).toFixed(2)}px)`;
      }
    }
  }

  // ---------- HUD
  const CH = Film.chapters;
  CH.forEach((c, i) => {
    const b = document.createElement('button');
    b.className = 'tick'; b.style.left = (c.start / DUR * 100) + '%';
    b.setAttribute('aria-label', `Chapter ${i + 1}: ${c.title}`); b.title = c.title;
    b.addEventListener('click', e => { e.stopPropagation(); seek(c.start + 0.01); });
    track.appendChild(b);
  });
  track.addEventListener('click', e => { const r = track.getBoundingClientRect(); seek((e.clientX - r.left) / r.width * DUR); });
  track.tabIndex = 0;
  track.addEventListener('keydown', e => { if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { e.preventDefault(); e.stopPropagation(); seek(clockT() + (e.key === 'ArrowRight' ? 5 : -5)); } });
  const chapterAt = t => { let k = 0; for (let i = 0; i < CH.length; i++) if (t >= CH[i].start) k = i; return k; };
  let hudTimer = 0;
  function showHud() { hud.classList.add('show'); document.body.classList.add('hud-on'); document.body.classList.remove('idle'); clearTimeout(hudTimer); hudTimer = setTimeout(() => { if (P.playing) { hud.classList.remove('show'); document.body.classList.remove('hud-on'); document.body.classList.add('idle'); } }, 2600); }
  ['pointermove', 'pointerdown', 'keydown'].forEach(e => window.addEventListener(e, () => P.started && showHud(), { passive: true }));

  btnPlay.addEventListener('click', e => { e.stopPropagation(); toggle(); });
  btnMute.addEventListener('click', e => { e.stopPropagation(); Sound.setMuted(!Sound.muted); btnMute.dataset.state = Sound.muted ? 'muted' : 'on'; btnMute.setAttribute('aria-label', Sound.muted ? 'Unmute' : 'Mute'); });
  btnFull.addEventListener('click', async e => {
    e.stopPropagation();
    try { if (!document.fullscreenElement) await document.documentElement.requestFullscreen(); else await document.exitFullscreen(); } catch (err) { }
  });
  if (!document.fullscreenEnabled) btnFull.hidden = true;

  function begin() {
    try { if (navigator.audioSession) navigator.audioSession.type = 'playback'; } catch (e) { }
    Sound.init();
    Sound.fadeIn();
    // the narration decodes in the background; if a line is already under way when it lands, join it
    Sound.voiceReady.then(ok => {
      if (!ok || !P.playing) return;
      const t = clockT();
      for (const ev of EV) if (ev.i === 'voice' && ev.t <= t && ev.t + ev.len > t + 0.3) Sound.play(ev, Sound.time + 0.03, t - ev.t);
    });
    intro.classList.add('gone');
    setTimeout(() => { intro.hidden = true; }, 1600);
    seek(0, false);
    play();
    showHud();
  }
  btnBegin.addEventListener('click', begin);
  btnAgain.addEventListener('click', () => { seek(0, false); play(); });

  window.addEventListener('keydown', e => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.target === track && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) return;
    if (!P.started) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); begin(); } return; }
    const key = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    if (key === ' ' || key === 'k') { e.preventDefault(); toggle(); }
    else if (e.key === 'ArrowRight') { const k = chapterAt(clockT()); if (k < CH.length - 1) seek(CH[k + 1].start + 0.01); }
    else if (e.key === 'ArrowLeft') { const t = clockT(), k = chapterAt(t); seek(t - CH[k].start > 2 || k === 0 ? CH[k].start + 0.01 : CH[k - 1].start + 0.01); }
    else if (key === 'm') btnMute.click();
    else if (key === 'f') btnFull.click();
  });
  // tap on the picture toggles playback (not on controls)
  cv.addEventListener('click', () => { if (P.started) toggle(); });
  document.addEventListener('visibilitychange', () => { if (document.hidden && P.playing) pause(); });

  const bloom = amount => FX.bloom(ctx, cv, amount);

  // ---------- adaptive quality
  let ftAvg = 16, ftN = 0, lastFrame = performance.now(), lowPower = false, refresh = 0, refreshS = [];
  function adapt(ft) {
    ftAvg = ftAvg * 0.95 + ft * 0.05; ftN++;
    if (!refresh) { refreshS.push(ft); if (refreshS.length >= 60) { refreshS.sort((a, b) => a - b); refresh = refreshS[30]; } return; }
    if (!P.playing) return;
    if (ftN > 90 && ftAvg > refresh * 1.4) { if (!lowPower) { lowPower = true; ftN = 0; } else if (dprCap > 0.6) { dprCap = Math.max(0.6, dprCap - 0.2); ftN = 0; resize(); } }
  }

  // ---------- main loop
  function frame(ts) {
    const ft = ts - lastFrame; lastFrame = ts;
    const dt = Math.min(0.05, ft / 1000);
    if (P.started && P.playing) {
      P.t = clockT();
      schedule(P.t);
      if (P.t >= DUR - 0.001) { P.playing = false; P.ended = true; endCard.hidden = false; btnPlay.dataset.state = 'paused'; btnPlay.setAttribute('aria-label', 'Play'); releaseWake(); setTimeout(() => { if (!P.playing) Sound.suspend(); }, 6000); showHud(); }
    }
    const t = P.t;
    if (P.playing || !P.started || dirty || t !== lastDrawT) {
      const fx = Film.render(ctx, P.started ? t : -1, dt, W, H, DPR, P.playing || !P.started);
      bloom(fx.bloom ?? 0.4);
      if (fx.tone && !lowPower) FX.tone(ctx, cv, fx.tone);
      const lb = (fx.letterbox ?? 0) * (W > H ? 1 : 0.35);
      const lbh = (lb * H * 0.105).toFixed(1) + 'px';
      lbT.style.height = lbh; lbB.style.height = lbh;
      lastDrawT = t; dirty = false;
    }
    if (Sound.ok) { const b = Film.beds(P.t), on = P.playing ? 1 : 0; Sound.setBeds((b.drone ?? 0) * on, (b.warmth ?? 0) * on, (b.wind ?? 0) * on, (b.cold ?? 0) * on, b.cut ?? 9000); }
    if (P.started) {
      updateCaptions(t);
      fill.style.transform = `scaleX(${(t / DUR).toFixed(4)})`;
      const k = chapterAt(t);
      if (chapLabel.dataset.k !== String(k)) { chapLabel.dataset.k = String(k); chapLabel.textContent = (CH[k].act ? CH[k].act + ' \u00b7 ' : '') + CH[k].title; }
      const sec = Math.round(t);
      if (track.dataset.s !== String(sec)) { track.dataset.s = String(sec); track.setAttribute('aria-valuenow', String(Math.round(t / DUR * 100))); track.setAttribute('aria-valuetext', `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`); }
    }
    if (ft < 200) adapt(ft);
    requestAnimationFrame(frame);
  }

  // film grain tile for the web (the export draws the same noise into each frame)
  try {
    const gc = document.createElement('canvas'); gc.width = gc.height = 256;
    const gg = gc.getContext('2d'), gd = gg.createImageData(256, 256), R = rng(77);
    for (let i = 0; i < gd.data.length; i += 4) { const v = (R() * 255) | 0; gd.data[i] = gd.data[i + 1] = gd.data[i + 2] = v; gd.data[i + 3] = 255; }
    gg.putImageData(gd, 0, 0);
    const gEl = document.getElementById('grain'); gEl.style.backgroundImage = `url(${gc.toDataURL()})`; gEl.style.backgroundSize = '256px';
  } catch (e) { }
  resize();
  requestAnimationFrame(frame);
  // test hook for automated visual QA (no effect on viewers)
  window.__film = { seek: t => { P.started = true; intro.hidden = true; P.playing = false; seek(t, false); }, get t() { return P.t; } };
})();
