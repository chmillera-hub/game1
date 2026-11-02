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
  // adaptive resolution: if frames run slow while playing, render fewer pixels
  const QUALITY = [1, 0.84, 0.7, 0.58];
  let qi = 0, slowFor = 0, fastFor = 0, costEMA = 8, gapEMA = 16.7, coolUntil = 0;
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
    const dpr = forcedSize ? 1 : Math.min(g.devicePixelRatio || 1, 2) * QUALITY[qi];
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
      const row = document.querySelector('.poster-row');
      const bar = (cssH * 139) / 1080, content = (row && row.offsetHeight) || 60;
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
    Art.grain(ctx, post.grain, Film.reducedMotion ? 0 : T);
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
  let wakeLock = null, wakeRefused = false;
  function requestWake() {
    if (wakeRefused || wakeLock || !navigator.wakeLock) return;
    try {
      const pp = document.permissionsPolicy || document.featurePolicy;
      if (pp && pp.allowsFeature && !pp.allowsFeature('screen-wake-lock')) { wakeRefused = true; return; }
      navigator.wakeLock.request('screen').then((w) => { wakeLock = w; w.addEventListener('release', () => { wakeLock = null; }); }).catch(() => { wakeRefused = true; });
    } catch (e) { wakeRefused = true; }
  }
  function releaseWake() { try { if (wakeLock) wakeLock.release(); } catch (e) { /* optional */ } wakeLock = null; }
  // the film clock runs from an anchor, so a slow frame drops frames instead of slowing the film
  let anchorT = 0, anchorNow = 0;
  const reanchor = () => { anchorT = Film.t; anchorNow = performance.now(); };
  Film.play = () => {
    if (Film.t >= Film.total - 0.05) Film.seek(0);
    reanchor();
    // films started without the Begin button (restored or deep-linked) still get sound
    if (g.FilmAudio && !Film.muted) { try { g.FilmAudio.init().then(() => g.FilmAudio.setMuted(Film.muted)).catch(() => {}); } catch (e) { /* audio optional */ } }
    Film.playing = true;
    Film.started = true;
    const st = document.getElementById('stage');
    if (st) st.classList.add('started');
    requestWake();
    ui.sync();
  };
  Film.pause = () => { Film.playing = false; releaseWake(); sharpen(); Film.dirty = true; ui.sync(); };
  Film.toggle = () => (Film.playing ? Film.pause() : Film.play());
  Film.seek = (T) => {
    Film.t = clamp(T, 0, Film.total);
    reanchor();
    Film._seeked = true;
    Film.dirty = true;
    ui.sync();
  };
  Film.jumpScene = (dir) => {
    const { i, lt } = Film.locate(Film.t);
    if (dir > 0 && i === Film.scenes.length - 1) { Film.seek(Film.total); return; }
    let j = i + dir;
    if (dir < 0 && lt > 2.5) j = i;
    j = clamp(j, 0, Film.scenes.length - 1);
    Film.seek(Film.scenes[j].start + 0.01);
  };
  function sharpen() { if (qi > 0 && !forcedSize) { qi = 0; Film.quality = 1; resize(); } }
  function adapt(dt, cost, now) {
    // judge the actual render work against the display's frame interval
    const gap = Math.min(250, dt * 1000);
    gapEMA = gapEMA * 0.9 + gap * 0.1;
    costEMA = costEMA * 0.9 + Math.min(250, cost) * 0.1;
    const interval = clamp(gapEMA, 8, 50);
    const slow = costEMA > 0.8 * Math.min(interval, 16.7) || gapEMA > 40;
    const fast = costEMA < 0.45 * Math.min(interval, 16.7) && gapEMA < 34;
    if (slow) { slowFor += dt; fastFor = 0; } else if (fast) { fastFor += dt; slowFor = Math.max(0, slowFor - dt); } else { slowFor = Math.max(0, slowFor - dt * 0.5); }
    if (slowFor > 1.2 && qi < QUALITY.length - 1) { qi++; slowFor = 0; coolUntil = now + 12000; resize(); }
    else if (fastFor > 6 && qi > 0 && now > coolUntil) { qi--; fastFor = 0; coolUntil = now + 6000; resize(); }
    Film.quality = QUALITY[qi];
  }
  function tick(now) {
    const dt = Math.max(0, Math.min(0.25, (now - last) / 1000 || 0));
    last = now;
    if (Film.playing) {
      let target = anchorT + ((now - anchorNow) / 1000) * Film.speed;
      if (target - Film.t > 0.5 || target < Film.t) { reanchor(); target = Film.t + Math.min(dt, 0.05) * Film.speed; anchorT = target; }
      Film.t = target;
      if (Film.t >= Film.total) { Film.t = Film.total; Film.playing = false; releaseWake(); sharpen(); ui.ended(); }
      Film.dirty = true;
    }
    ui.lift(dt);
    const w0 = performance.now();
    const drew = Film.dirty;
    if (Film.dirty) frame(Film.t);
    if (Film.playing && drew && !forcedSize && dt > 0) adapt(dt, performance.now() - w0, now);
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
  const ui = { sync() {}, tick() {}, ended() {}, lift() {} };
  function setupUI(opts) {
    const $ = (id) => document.getElementById(id);
    const stage = $('stage'), bar = $('bar'), poster = $('poster'), endCard = $('endcard');
    const playBtn = $('play'), track = $('track'), fill = $('fill'), knob = $('knob'), ticks = $('ticks'), tip = $('tip'), time = $('time'), chap = $('chap');
    const sndBtn = $('sound'), fsBtn = $('fs'), prevBtn = $('prev'), nextBtn = $('next'), beginBtn = $('begin'), sndChk = $('withsound'), againBtn = $('again');
    const live = $('live');
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
    let lastLive = '';
    const announce = (msg) => { if (live && msg !== lastLive) { live.textContent = msg; lastLive = msg; } };
    ui.sync = () => {
      const atEnd = Film.started && !Film.playing && Film.t >= Film.total - 0.05;
      endCard.hidden = !atEnd;
      stage.classList.toggle('playing', Film.playing);
      announce(atEnd ? 'The end' : Film.playing ? 'Playing' : Film.started ? 'Paused' : '');
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
      const { i } = Film.locate(Film.t);
      const title = Film.scenes[i] ? Film.scenes[i].title : '';
      if (sec !== lastSec) {
        time.textContent = U.fmtTime(Film.t) + ' / ' + dur;
        lastSec = sec;
        if (!Film.playing || sec % 5 === 0) { track.setAttribute('aria-valuenow', String(sec)); track.setAttribute('aria-valuetext', U.fmtTime(Film.t) + ' of ' + dur + ', ' + title); }
      }
      if (title !== lastChap) { chap.textContent = title; lastChap = title; if (Film.started && Film.playing) announce(title); }
    };
    ui.ended = () => { ui.sync(); showBar(); try { againBtn.focus({ preventScroll: true }); } catch (e) { /* optional */ } };
    // lift the narration out of the way while the control bar overlaps the bottom letterbox
    let lift = 0;
    ui.lift = (dt) => {
      let want = 0;
      const shown = Film.started && (stage.classList.contains('active') || !Film.playing || stage.matches(':focus-within'));
      if (shown && !bar.hidden) {
        const r = canvas.getBoundingClientRect(), b = bar.getBoundingClientRect();
        const sc = r.height / H;
        const capBottom = r.top + 1064 * sc, barTop = b.top + 20;
        if (sc > 0) want = clamp((capBottom - barTop) / sc, 0, 150);
      }
      const nl = lift + (want - lift) * Math.min(1, (dt || 0.016) * 9);
      if (Math.abs(nl - lift) > 0.05 || (want === 0 && lift !== 0 && Math.abs(nl) < 0.3)) { lift = Math.abs(nl) < 0.3 && want === 0 ? 0 : nl; Art.captionLift = lift; Film.dirty = true; }
    };
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
    let lastPointer = 'mouse';
    stage.addEventListener('pointermove', (ev) => { if (ev.pointerType === 'mouse') showBar(); });
    stage.addEventListener('pointerdown', (ev) => { lastPointer = ev.pointerType || 'mouse'; if (lastPointer === 'mouse') showBar(); }, true);
    bar.addEventListener('pointerenter', () => { clearTimeout(idleTimer); stage.classList.add('active'); });
    bar.addEventListener('focusin', () => { clearTimeout(idleTimer); stage.classList.add('active'); });
    bar.addEventListener('focusout', showBar);

    let beginning = false;
    const begin = async () => {
      if (beginning || Film.started) return;
      beginning = true;
      poster.hidden = true;
      Film.muted = !(sndChk ? sndChk.checked : true);
      if (g.FilmAudio && !Film.muted) { try { await g.FilmAudio.init(); g.FilmAudio.setMuted(false); } catch (e) { console.warn('audio unavailable', e); } }
      Film.seek(0);
      Film.play();
      showBar();
      beginning = false;
    };
    ui.begin = begin;
    beginBtn.addEventListener('click', begin);
    againBtn.addEventListener('click', () => { Film.seek(0); Film.play(); });
    playBtn.addEventListener('click', (e) => { e.stopPropagation(); if (!Film.started) return begin(); Film.toggle(); });
    prevBtn.addEventListener('click', (e) => { e.stopPropagation(); Film.jumpScene(-1); });
    nextBtn.addEventListener('click', (e) => { e.stopPropagation(); Film.jumpScene(1); });
    const setMuted = async (m) => {
      Film.muted = m;
      if (g.FilmAudio) { try { if (!m) await g.FilmAudio.init(); g.FilmAudio.setMuted(m); } catch (e) { /* ignore */ } }
      ui.sync();
    };
    sndBtn.addEventListener('click', (e) => { e.stopPropagation(); setMuted(!Film.muted); });
    const reqFs = stage.requestFullscreen || stage.webkitRequestFullscreen;
    const canFs = !!reqFs && (document.fullscreenEnabled !== false || document.webkitFullscreenEnabled === true);
    if (!canFs) fsBtn.hidden = true;
    const toggleFs = () => {
      if (!canFs) return;
      try {
        if (document.fullscreenElement || document.webkitFullscreenElement) (document.exitFullscreen || document.webkitExitFullscreen).call(document);
        else { const r = reqFs.call(stage); if (r && r.catch) r.catch(() => {}); }
      } catch (e) { /* optional */ }
    };
    fsBtn.addEventListener('click', (e) => { e.stopPropagation(); toggleFs(); });
    document.addEventListener('fullscreenchange', () => setTimeout(resize, 50));
    document.addEventListener('webkitfullscreenchange', () => setTimeout(resize, 50));
    // mouse: click pauses (debounced so a double-click only toggles fullscreen); touch: tap shows/hides controls
    let clickTimer = 0;
    canvas.addEventListener('click', (ev) => {
      if (!Film.started) return;
      if (lastPointer !== 'mouse') {
        if (stage.classList.contains('active') && Film.playing) { clearTimeout(idleTimer); stage.classList.remove('active'); } else showBar();
        return;
      }
      clearTimeout(clickTimer);
      if (ev.detail > 1) return;
      clickTimer = setTimeout(() => { Film.toggle(); showBar(); }, 240);
    });
    canvas.addEventListener('dblclick', () => { clearTimeout(clickTimer); toggleFs(); });

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
    let resumeAfterDrag = false;
    const endDrag = () => {
      if (!dragging) return;
      dragging = false;
      if (resumeAfterDrag && Film.t < Film.total - 0.05) { Film.playing = true; reanchor(); ui.sync(); }
      resumeAfterDrag = false;
    };
    track.addEventListener('pointerdown', (ev) => {
      if (ev.button !== 0) return;
      if (!Film.started) { Film.started = true; poster.hidden = true; stage.classList.add('started'); }
      dragging = true;
      resumeAfterDrag = Film.playing;
      Film.playing = false; // hold the picture under the finger without releasing the wake lock
      try { track.setPointerCapture(ev.pointerId); } catch (e) { /* optional */ }
      Film.seek(posToT(ev));
    });
    track.addEventListener('pointermove', (ev) => { hover(ev); if (dragging) Film.seek(posToT(ev)); });
    track.addEventListener('pointerup', endDrag);
    track.addEventListener('pointercancel', endDrag);
    track.addEventListener('lostpointercapture', endDrag);
    track.addEventListener('pointerleave', () => { if (!dragging) tip.hidden = true; });
    track.addEventListener('keydown', (ev) => {
      if (ev.shiftKey || ev.ctrlKey || ev.metaKey || ev.altKey) return;
      const k = ev.key;
      let T = null;
      if (k === 'ArrowRight' || k === 'ArrowUp') T = Film.t + 5;
      else if (k === 'ArrowLeft' || k === 'ArrowDown') T = Film.t - 5;
      else if (k === 'PageUp') T = Film.t + 30;
      else if (k === 'PageDown') T = Film.t - 30;
      else if (k === 'Home') T = 0;
      else if (k === 'End') T = Film.total;
      if (T !== null) { Film.seek(T); ev.preventDefault(); ev.stopPropagation(); showBar(); }
    });

    // keyboard
    document.addEventListener('keydown', (ev) => {
      if (ev.ctrlKey || ev.metaKey || ev.altKey || ev.defaultPrevented) return;
      const tgt = ev.target;
      if (tgt && (/TEXTAREA|SELECT/.test(tgt.tagName) || (tgt.tagName === 'INPUT' && !/^(checkbox|radio|range|button)$/.test(tgt.type)) || tgt.isContentEditable)) return;
      const key = ev.key;
      // let a focused button handle its own Space/Enter
      if ((key === ' ' || key === 'Enter') && tgt && tgt.closest && tgt.closest('button')) return;
      if (ev.repeat && /^[ kKmMfFnNpP]$/.test(key)) { ev.preventDefault(); return; }
      if (!Film.started) {
        if (key === ' ' || key === 'Enter' || key === 'k' || key === 'K') { ev.preventDefault(); begin(); }
        return;
      }
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
    if (Film._pendingBegin) { Film._pendingBegin = false; begin(); }
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
    Art.reducedMotion = Film.reducedMotion;
    // a click on Begin while fonts are still loading is remembered (and unlocks audio inside the gesture)
    const early = document.getElementById('begin');
    const earlyClick = () => {
      if (Film.ready) return;
      Film._pendingBegin = true;
      const chk = document.getElementById('withsound');
      try { if (g.FilmAudio && (!chk || chk.checked)) g.FilmAudio.init().catch(() => {}); } catch (e) { /* optional */ }
    };
    if (early && !test) early.addEventListener('click', earlyClick);
    await loadFonts();
    if (early) early.removeEventListener('click', earlyClick);
    Film.ready = true;
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
