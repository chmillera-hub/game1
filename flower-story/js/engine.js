/* ==========================================================================
   engine.js — timeline, rendering pipeline, transitions, player UI.
   Global: Film
   A scene registers itself with Film.scene({...}). The whole film is a pure
   function of time T, so seeking/scrubbing always works.
   ========================================================================== */
(function (g) {
  'use strict';
  const { W, H, clamp } = U;

  const Film = {
    scenes: [],
    total: 0,
    t: 0,
    playing: false,
    speed: 1,
    muted: false,
    started: false,
    errors: [],
    reducedMotion: !!(g.matchMedia && g.matchMedia('(prefers-reduced-motion: reduce)').matches),
  };
  const DEFAULTS = { fadeIn: 0.8, fadeOut: 0.8, crossIn: 0, fadeColor: '#000000' };
  const POST = { vignette: 0.32, grain: 0.045, letterbox: 1 };

  /**
   * Register a scene.
   * def = {
   *   id, order, title, duration,
   *   chapter?: 'Part One · The Trail'   (shown briefly in the top bar)
   *   mood?: 'forest' ...                 (audio ambience/music)
   *   sfx?: [[localT, 'id', {gain}], ...] (audio cues)
   *   fadeIn?, fadeOut? (seconds, to fadeColor), crossIn? (seconds crossfade from previous)
   *   post?: {vignette, grain, letterbox} or (t) => ({...})
   *   render(ctx, t, S)  — t = local seconds (may exceed duration by up to ~2s during crossfades)
   * }
   */
  Film.scene = (def) => {
    Film.scenes.push(Object.assign({}, DEFAULTS, def));
    Film._dirtyLayout = true;
  };

  function layout() {
    Film.scenes.sort((a, b) => a.order - b.order);
    let t = 0;
    for (const s of Film.scenes) { s.start = t; t += s.duration; }
    Film.total = t;
    Film._dirtyLayout = false;
  }
  Film.layout = layout;
  Film.locate = (T) => {
    const sc = Film.scenes;
    for (let i = 0; i < sc.length; i++) if (T < sc[i].start + sc[i].duration || i === sc.length - 1) return { i, lt: T - sc[i].start };
    return { i: 0, lt: 0 };
  };
  Film.sceneStart = (id) => { const s = Film.scenes.find((x) => x.id === id); return s ? s.start : 0; };

  /* ---------------- canvas ---------------- */
  let canvas, ctx, buf, bctx, k = 1;
  let forcedSize = null;
  function resize() {
    const stage = document.getElementById('stage');
    const vw = stage ? stage.clientWidth : g.innerWidth, vh = stage ? stage.clientHeight : g.innerHeight;
    let cssW, cssH;
    if (forcedSize) { cssW = forcedSize[0]; cssH = forcedSize[1]; } else {
      const fit = Math.min(vw / W, vh / H);
      cssW = Math.max(1, Math.floor(W * fit)); cssH = Math.max(1, Math.floor(H * fit));
    }
    canvas.style.width = cssW + 'px';
    canvas.style.height = cssH + 'px';
    const dpr = forcedSize ? 1 : Math.min(g.devicePixelRatio || 1, 2);
    let pw = Math.round(cssW * dpr), ph = Math.round(cssH * dpr);
    const maxW = 2560;
    if (pw > maxW) { ph = Math.round((ph * maxW) / pw); pw = maxW; }
    for (const c of [canvas, buf]) { if (c.width !== pw || c.height !== ph) { c.width = pw; c.height = ph; } }
    k = pw / W;
    Art._base = new DOMMatrix([k, 0, 0, k, 0, 0]);
    Film.dirty = true;
    // seat the start controls inside the film's bottom letterbox bar (or just below the film)
    if (stage) {
      const below = Math.max(0, (vh - cssH) / 2);
      const bar = (cssH * 139) / 1080, content = 60;
      let pb = below + (bar - content) / 2;
      if (bar < content + 6) pb = below >= content + 32 ? below - content - 20 : 12;
      stage.style.setProperty('--poster-pb', Math.round(pb) + 'px');
    }
  }

  /* ---------------- rendering ---------------- */
  function reportError(sc, e) {
    const msg = (e && e.message) || String(e);
    const key = sc.id + ':' + msg;
    if (!Film._seenErr) Film._seenErr = new Set();
    if (!Film._seenErr.has(key)) {
      Film._seenErr.add(key);
      Film.errors.push({ scene: sc.id, message: msg, stack: e && e.stack });
      console.error('[scene ' + sc.id + ']', e);
    }
  }
  function drawScene(c, i, lt, T) {
    const sc = Film.scenes[i];
    c.save();
    c.globalAlpha = 1;
    c.globalCompositeOperation = 'source-over';
    try {
      sc.render(c, lt, { d: sc.duration, T, i, p: lt / sc.duration, id: sc.id, scene: sc, W, H });
    } catch (e) { reportError(sc, e); }
    c.restore();
  }
  function postOf(sc, lt) {
    const p = typeof sc.post === 'function' ? sc.post(lt) : sc.post;
    return Object.assign({}, POST, p || {});
  }
  function frame(T) {
    if (Film._dirtyLayout) layout();
    if (!Film.scenes.length) return;
    const base = Art._base;
    ctx.setTransform(base);
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, W, H);
    Art._overlay = [];
    const { i, lt } = Film.locate(T);
    const sc = Film.scenes[i];
    const next = Film.scenes[i + 1];
    const cross = sc.crossIn > 0 && i > 0 && lt < sc.crossIn;
    let post = postOf(sc, lt);
    if (cross) {
      const prev = Film.scenes[i - 1];
      const mix = U.smooth(lt / sc.crossIn);
      Art._alpha = 1 - mix;
      drawScene(ctx, i - 1, prev.duration + lt, T);
      bctx.setTransform(1, 0, 0, 1, 0, 0);
      bctx.clearRect(0, 0, buf.width, buf.height);
      bctx.setTransform(base);
      Art._alpha = mix;
      drawScene(bctx, i, lt, T);
      ctx.save();
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.globalAlpha = mix;
      ctx.drawImage(buf, 0, 0);
      ctx.restore();
      post = U.mixDeep(postOf(prev, prev.duration + lt), post, mix);
    } else {
      Art._alpha = 1;
      drawScene(ctx, i, lt, T);
    }
    // post FX
    ctx.save();
    ctx.setTransform(base);
    Art.vignette(ctx, post.vignette);
    Art.grain(ctx, post.grain, T);
    Art.letterbox(ctx, post.letterbox);
    // fades
    let fade = 0, fadeColor = sc.fadeColor;
    if (!cross && !sc.crossIn && sc.fadeIn > 0 && lt < sc.fadeIn) fade = Math.max(fade, 1 - U.smooth(lt / sc.fadeIn));
    if (sc.fadeOut > 0 && !(next && next.crossIn) && lt > sc.duration - sc.fadeOut) fade = Math.max(fade, 1 - U.smooth((sc.duration - lt) / sc.fadeOut));
    if (fade > 0.001) {
      ctx.globalAlpha = fade;
      ctx.fillStyle = fadeColor;
      ctx.fillRect(0, 0, W, H);
      ctx.globalAlpha = 1;
    }
    // overlay (captions, titles) above post
    for (const item of Art._overlay) {
      ctx.save();
      ctx.globalAlpha = item.a * (1 - fade);
      try { item.fn(ctx); } catch (e) { reportError(sc, e); }
      ctx.restore();
    }
    Art._overlay = [];
    // chapter label in the top bar
    if (sc.chapter) {
      const a = U.fade(lt, 0.9, 6.2, 1.0, 1.2) * (1 - fade);
      if (a > 0.01) {
        ctx.save();
        ctx.globalAlpha = a * 0.78;
        ctx.font = Art.font(21, 'sans', 700);
        ctx.fillStyle = '#efe4d2';
        ctx.textBaseline = 'middle';
        const label = sc.chapter.toUpperCase();
        let x = 84;
        for (const ch of label) { ctx.fillText(ch, x, 70); x += ctx.measureText(ch).width + 3.2; }
        ctx.globalAlpha = a * 0.6;
        ctx.fillStyle = '#ff6f9c';
        ctx.beginPath(); ctx.arc(66, 70, 4, 0, U.TAU); ctx.fill();
        ctx.restore();
      }
    }
    ctx.restore();
    Film.dirty = false;
    Film.frameCount = (Film.frameCount || 0) + 1;
  }
  Film.renderAt = (T) => { Film.t = clamp(T, 0, Film.total); frame(Film.t); };

  /* ---------------- playback ---------------- */
  let last = 0;
  let wakeLock = null;
  function requestWake() {
    try { if (navigator.wakeLock && !wakeLock) navigator.wakeLock.request('screen').then((w) => { wakeLock = w; w.addEventListener('release', () => { wakeLock = null; }); }).catch(() => {}); } catch (e) { /* optional */ }
  }
  function releaseWake() { try { if (wakeLock) wakeLock.release(); } catch (e) { /* optional */ } wakeLock = null; }
  Film.play = () => {
    if (Film.t >= Film.total - 0.05) Film.seek(0);
    Film.playing = true;
    Film.started = true;
    const st = document.getElementById('stage');
    if (st) st.classList.add('started');
    requestWake();
    ui.sync();
  };
  Film.pause = () => { Film.playing = false; releaseWake(); Film.dirty = true; ui.sync(); };
  Film.toggle = () => (Film.playing ? Film.pause() : Film.play());
  Film.seek = (T) => {
    Film.t = clamp(T, 0, Film.total);
    Film._seeked = true;
    Film.dirty = true;
    ui.sync();
  };
  Film.jumpScene = (dir) => {
    const { i, lt } = Film.locate(Film.t);
    let j = i + dir;
    if (dir < 0 && lt > 2.5) j = i;
    j = clamp(j, 0, Film.scenes.length - 1);
    Film.seek(Film.scenes[j].start + 0.01);
  };
  function tick(now) {
    const dt = Math.min(0.1, (now - last) / 1000 || 0);
    last = now;
    if (Film.playing) {
      Film.t += dt * Film.speed;
      if (Film.t >= Film.total) { Film.t = Film.total; Film.playing = false; releaseWake(); ui.ended(); }
      Film.dirty = true;
    }
    if (Film.dirty) frame(Film.t);
    if (g.FilmAudio && Film.started) {
      const { i, lt } = Film.locate(Film.t);
      try {
        g.FilmAudio.update({ T: Film.t, playing: Film.playing, i, lt, scene: Film.scenes[i], scenes: Film.scenes, seeked: !!Film._seeked, speed: Film.speed, dt });
      } catch (e) { if (!Film._audioErr) { Film._audioErr = true; console.error('[audio]', e); } }
    }
    Film._seeked = false;
    ui.tick();
    requestAnimationFrame(tick);
  }

  /* ---------------- UI ---------------- */
  const ui = { sync() {}, tick() {}, ended() {} };
  function setupUI(opts) {
    const $ = (id) => document.getElementById(id);
    const stage = $('stage'), bar = $('bar'), poster = $('poster'), endCard = $('endcard');
    const playBtn = $('play'), track = $('track'), fill = $('fill'), knob = $('knob'), ticks = $('ticks'), tip = $('tip'), time = $('time'), chap = $('chap');
    const sndBtn = $('sound'), fsBtn = $('fs'), prevBtn = $('prev'), nextBtn = $('next'), beginBtn = $('begin'), sndChk = $('withsound'), againBtn = $('again');
    if (!stage) return;
    if (opts.test) { [bar, poster, endCard].forEach((e) => e && (e.hidden = true)); return; }

    // chapter ticks
    ticks.innerHTML = '';
    Film.scenes.forEach((s, i) => {
      if (i === 0) return;
      const d = document.createElement('span');
      d.className = 'tick' + (s.chapter ? ' major' : '');
      d.style.left = (s.start / Film.total) * 100 + '%';
      ticks.appendChild(d);
    });
    const dur = U.fmtTime(Film.total);
    let lastSec = -1, lastChap = '';
    ui.sync = () => {
      stage.classList.toggle('playing', Film.playing);
      playBtn.setAttribute('aria-label', Film.playing ? 'Pause' : 'Play');
      playBtn.dataset.state = Film.playing ? 'pause' : 'play';
      sndBtn.dataset.state = Film.muted ? 'off' : 'on';
      sndBtn.setAttribute('aria-label', Film.muted ? 'Unmute' : 'Mute');
      lastSec = -1;
      ui.tick();
    };
    ui.tick = () => {
      const p = Film.total ? Film.t / Film.total : 0;
      fill.style.transform = `scaleX(${p})`;
      knob.style.left = p * 100 + '%';
      const sec = Math.floor(Film.t);
      if (sec !== lastSec) { time.textContent = U.fmtTime(Film.t) + ' / ' + dur; lastSec = sec; track.setAttribute('aria-valuenow', String(sec)); }
      const { i } = Film.locate(Film.t);
      const title = Film.scenes[i] ? Film.scenes[i].title : '';
      if (title !== lastChap) { chap.textContent = title; lastChap = title; }
    };
    ui.ended = () => { endCard.hidden = false; showBar(); ui.sync(); };
    track.setAttribute('aria-valuemax', String(Math.floor(Film.total)));
    const rt = $('runtime');
    const mins = Math.max(1, Math.round(Film.total / 60));
    if (rt) rt.textContent = 'About ' + mins + (mins === 1 ? ' minute' : ' minutes');

    // idle-hide controls
    let idleTimer = 0;
    const showBar = () => {
      stage.classList.add('active');
      clearTimeout(idleTimer);
      idleTimer = setTimeout(() => { if (Film.playing) stage.classList.remove('active'); }, 2600);
    };
    stage.addEventListener('pointermove', showBar);
    stage.addEventListener('pointerdown', showBar);
    bar.addEventListener('pointerenter', () => { clearTimeout(idleTimer); stage.classList.add('active'); });

    const begin = async () => {
      poster.hidden = true;
      endCard.hidden = true;
      Film.muted = !(sndChk ? sndChk.checked : true);
      if (g.FilmAudio) { try { await g.FilmAudio.init(); g.FilmAudio.setMuted(Film.muted); } catch (e) { console.warn('audio unavailable', e); } }
      Film.seek(0);
      Film.play();
      showBar();
    };
    beginBtn.addEventListener('click', begin);
    againBtn.addEventListener('click', () => { endCard.hidden = true; Film.seek(0); Film.play(); });
    playBtn.addEventListener('click', (e) => { e.stopPropagation(); if (!Film.started) return begin(); Film.toggle(); });
    prevBtn.addEventListener('click', (e) => { e.stopPropagation(); Film.jumpScene(-1); });
    nextBtn.addEventListener('click', (e) => { e.stopPropagation(); Film.jumpScene(1); });
    const setMuted = async (m) => {
      Film.muted = m;
      if (g.FilmAudio) { try { if (!m) await g.FilmAudio.init(); g.FilmAudio.setMuted(m); } catch (e) { /* ignore */ } }
      ui.sync();
    };
    sndBtn.addEventListener('click', (e) => { e.stopPropagation(); setMuted(!Film.muted); });
    const toggleFs = () => {
      try {
        if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
        else if (stage.requestFullscreen) stage.requestFullscreen().catch(() => {});
      } catch (e) { /* optional */ }
    };
    fsBtn.addEventListener('click', (e) => { e.stopPropagation(); toggleFs(); });
    document.addEventListener('fullscreenchange', () => setTimeout(resize, 50));
    canvas.addEventListener('click', () => { if (!Film.started) return; Film.toggle(); showBar(); });
    canvas.addEventListener('dblclick', toggleFs);

    // scrubbing
    let dragging = false;
    const posToT = (ev) => {
      const r = track.getBoundingClientRect();
      return clamp((ev.clientX - r.left) / r.width) * Film.total;
    };
    const hover = (ev) => {
      const T = posToT(ev);
      const { i } = Film.locate(T);
      const r = track.getBoundingClientRect();
      tip.textContent = U.fmtTime(T) + ' · ' + Film.scenes[i].title;
      tip.style.left = clamp((ev.clientX - r.left) / r.width) * 100 + '%';
      tip.hidden = false;
    };
    track.addEventListener('pointerdown', (ev) => {
      if (!Film.started) { Film.started = true; poster.hidden = true; }
      dragging = true;
      track.setPointerCapture(ev.pointerId);
      Film.seek(posToT(ev));
      endCard.hidden = true;
    });
    track.addEventListener('pointermove', (ev) => { hover(ev); if (dragging) Film.seek(posToT(ev)); });
    track.addEventListener('pointerup', () => { dragging = false; });
    track.addEventListener('pointerleave', () => { if (!dragging) tip.hidden = true; });
    track.addEventListener('keydown', (ev) => {
      if (ev.key === 'ArrowRight') { Film.seek(Film.t + 5); ev.preventDefault(); ev.stopPropagation(); }
      if (ev.key === 'ArrowLeft') { Film.seek(Film.t - 5); ev.preventDefault(); ev.stopPropagation(); }
    });

    // keyboard
    document.addEventListener('keydown', (ev) => {
      if (ev.target && /INPUT|TEXTAREA|SELECT/.test(ev.target.tagName)) return;
      const key = ev.key;
      if (!Film.started && (key === ' ' || key === 'Enter')) { ev.preventDefault(); begin(); return; }
      if (key === ' ' || key === 'k' || key === 'K') { ev.preventDefault(); Film.toggle(); }
      else if (key === 'ArrowRight') { ev.preventDefault(); ev.shiftKey ? Film.jumpScene(1) : Film.seek(Film.t + 5); }
      else if (key === 'ArrowLeft') { ev.preventDefault(); ev.shiftKey ? Film.jumpScene(-1) : Film.seek(Film.t - 5); }
      else if (key === 'l' || key === 'L') Film.seek(Film.t + 10);
      else if (key === 'j' || key === 'J') Film.seek(Film.t - 10);
      else if (key === 'n' || key === 'N' || key === 'PageDown') Film.jumpScene(1);
      else if (key === 'p' || key === 'P' || key === 'PageUp') Film.jumpScene(-1);
      else if (key === 'm' || key === 'M') setMuted(!Film.muted);
      else if (key === 'f' || key === 'F') toggleFs();
      else if (key === 'Home') Film.seek(0);
      else if (/^[0-9]$/.test(key)) Film.seek((+key / 10) * Film.total);
      else return;
      showBar();
    });
    document.addEventListener('visibilitychange', () => { if (document.hidden && Film.playing) Film.pause(); });
    ui.sync();
  }

  /* ---------------- boot ---------------- */
  async function loadFonts() {
    if (!document.fonts || !document.fonts.load) return;
    const faces = [
      'italic 500 48px "Cormorant Garamond"', 'italic 600 48px "Cormorant Garamond"', '500 48px "Cormorant Garamond"',
      '700 32px "Nunito"', '800 32px "Nunito"', '700 48px "Caveat"',
    ];
    const timeout = new Promise((r) => setTimeout(r, 3500));
    try { await Promise.race([Promise.all(faces.map((f) => document.fonts.load(f))), timeout]); } catch (e) { /* fallback fonts */ }
    Art.clearTextCache();
  }

  Film.boot = async (restored = {}) => {
    canvas = document.getElementById('film');
    ctx = canvas.getContext('2d');
    buf = document.createElement('canvas');
    bctx = buf.getContext('2d');
    const q = new URLSearchParams(location.search);
    const test = q.has('test');
    if (q.has('w')) forcedSize = [+q.get('w'), Math.round((+q.get('w') * H) / W)];
    layout();
    resize();
    g.addEventListener('resize', resize);
    await loadFonts();
    setupUI({ test });
    // initial time: test params, hot-reload snapshot, or the poster frame
    let T0 = null;
    if (q.has('scene')) T0 = Film.sceneStart(q.get('scene')) + (+q.get('lt') || 0);
    if (q.has('t')) T0 = +q.get('t');
    if (T0 !== null) {
      Film.started = true;
      const poster = document.getElementById('poster');
      if (poster) poster.hidden = true;
      Film.seek(T0);
    } else if (restored && typeof restored.t === 'number' && restored.t > 0) {
      Film.started = true;
      document.getElementById('stage').classList.add('started');
      const poster = document.getElementById('poster');
      if (poster) poster.hidden = true;
      Film.seek(restored.t);
    } else {
      const posterT = Film.scenes[0] ? Film.scenes[0].start + (Film.scenes[0].poster || Math.min(7.5, Film.scenes[0].duration * 0.6)) : 0;
      Film.renderAt(posterT);
      Film.t = posterT;
    }
    if (q.has('autoplay')) Film.play();
    frame(Film.t);
    try { if (g.claude && g.claude.hot && g.claude.hot.snapshot) g.claude.hot.snapshot(() => ({ t: Film.t })); } catch (e) { /* not in a viewer */ }
    last = performance.now();
    requestAnimationFrame(tick);
    Film.ready = true;
  };

  // test / automation hooks
  g.FILM = {
    get duration() { return Film.total; },
    get scenes() { return Film.scenes.map((s) => ({ id: s.id, order: s.order, title: s.title, start: s.start, duration: s.duration })); },
    get errors() { return Film.errors; },
    renderAt: (T) => Film.renderAt(T),
    sceneStart: (id) => Film.sceneStart(id),
    canvas: () => canvas,
  };
  g.Film = Film;
})(window);
