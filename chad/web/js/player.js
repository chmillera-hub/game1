/* FLEECED - player: font loading, frame compositing, audio-clocked playback, render hook. */
(function () {
  'use strict';
  const { W, H, TL, clamp } = F;
  const RENDER = /[?&]render\b/.test(location.search);

  // ---------------------------------------------------------------- fonts
  const ready = (async () => {
    const src = window.FLEECED_FONTS || {};
    const faces = [];
    if (src.fredoka) faces.push(new FontFace('Fredoka', `url(${src.fredoka})`, { weight: '300 700' }));
    if (src.luckiest) faces.push(new FontFace('Luckiest Guy', `url(${src.luckiest})`));
    await Promise.all(faces.map(f => f.load().then(ff => document.fonts.add(ff)).catch(() => {})));
  })();
  window.fleecedReady = ready;

  // ---------------------------------------------------------------- frame
  let vignette = null;
  function renderFrame(ctx, t, opts = {}) {
    const scale = opts.scale || 1;
    t = clamp(t, 0, TL.duration - 0.001);
    ctx.save();
    ctx.setTransform(scale, 0, 0, scale, 0, 0);
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, W, H);
    const sc = TL.scenes[F.sceneAt(t)];
    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, W, H);
    ctx.clip();
    window.SCENES[sc.id](ctx, t, sc);
    ctx.restore();
    window.A.tint.k = 0;
    if (!vignette) {
      vignette = ctx.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, H * 1.05);
      vignette.addColorStop(0, 'rgba(0,0,0,0)');
      vignette.addColorStop(1, 'rgba(0,0,0,0.32)');
    }
    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, W, H);
    if (opts.captions !== false) F.subtitles(ctx, t);
    ctx.restore();
  }
  window.renderFrame = renderFrame;

  const canvas = document.getElementById('film');
  const ctx = canvas.getContext('2d');

  // ---------------------------------------------------------------- headless render hook
  if (RENDER) {
    document.documentElement.classList.add('render');
    canvas.width = W;
    canvas.height = H;
    window.renderAt = (t) => { renderFrame(ctx, t, { scale: 1 }); return true; };
    return;
  }

  // ---------------------------------------------------------------- player
  const $ = (id) => document.getElementById(id);
  const audio = $('audio');
  const stage = $('stage');
  const overlay = $('overlay');
  const playBtn = $('play');
  const scrub = $('scrub');
  const timeEl = $('time');
  const ccBtn = $('cc');
  const fsBtn = $('fs');
  const chapList = $('chapters');
  let captions = true;
  let scale = 1;
  let dragging = false;

  const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  $('runtime').textContent = fmt(TL.duration);
  $('total').textContent = fmt(TL.duration);

  // chapters
  const CHAPTERS = [
    ['charge', 'Powering up'], ['village', 'Meanwhile, in the village'], ['meet', 'The Omega God level'], ['pang', 'A pang of sadness'],
    ['golf', 'Mini-golf'], ['voicemail', 'The universe martial artist'], ['dinner', 'Dinner time'],
  ];
  const starts = Object.fromEntries(TL.scenes.map(s => [s.id, s.start]));
  const chapters = CHAPTERS.map(([id, name]) => ({ id, name, t: starts[id] }));
  const ticks = $('ticks');
  chapters.forEach((ch, i) => {
    const tick = document.createElement('span');
    tick.className = 'tick';
    tick.style.left = (ch.t / TL.duration) * 100 + '%';
    ticks.appendChild(tick);
    const li = document.createElement('li');
    const b = document.createElement('button');
    b.type = 'button';
    b.innerHTML = `<span class="n">${String(i + 1).padStart(2, '0')}</span><span class="nm">${ch.name}</span><span class="tc">${fmt(ch.t)}</span>`;
    b.addEventListener('click', () => { seek(ch.t + 0.01); start(); });
    li.appendChild(b);
    chapList.appendChild(li);
    ch.el = b;
  });

  // clock: audio time, smoothed between coarse currentTime updates
  let lastCT = -1, anchorT = 0, anchorWall = 0;
  function now() {
    const ct = audio.currentTime;
    if (audio.paused || audio.seeking) { lastCT = ct; return ct; }
    if (ct !== lastCT) { lastCT = ct; anchorT = ct; anchorWall = performance.now(); }
    return Math.min(anchorT + (performance.now() - anchorWall) / 1000, ct + 0.3);
  }

  function resize() {
    const r = canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = Math.max(320, Math.min(W, Math.round(r.width * dpr)));
    if (canvas.width !== w) {
      canvas.width = w;
      canvas.height = Math.round((w * H) / W);
      vignette = null;
    }
    scale = canvas.width / W;
  }

  // poster frame: the title card; on narrow screens a moment later, when the title has risen above the play button
  let poster = window.matchMedia('(max-width: 560px)').matches ? 3.75 : 2.3;
  function draw() {
    const playing = !audio.paused;
    const t = playing || audio.currentTime > 0 ? now() : poster;
    renderFrame(ctx, t, { scale, captions });
    if (!dragging) scrub.value = String(Math.round((audio.currentTime / TL.duration) * 1000));
    timeEl.textContent = fmt(audio.currentTime);
    let cur = -1;
    chapters.forEach((ch, i) => { if (audio.currentTime >= ch.t - 0.01) cur = i; });
    chapters.forEach((ch, i) => ch.el.classList.toggle('on', i === cur && audio.currentTime > 0));
  }
  function loop() {
    draw();
    requestAnimationFrame(loop);
  }

  function setPlaying(p) {
    playBtn.setAttribute('aria-label', p ? 'Pause' : 'Play');
    playBtn.classList.toggle('playing', p);
    stage.classList.toggle('is-playing', p);
  }
  async function start() {
    overlay.hidden = true;
    try { await audio.play(); } catch (err) { overlay.hidden = false; $('overlay-note').textContent = 'Tap play to start the sound.'; }
  }
  function toggle() {
    if (audio.paused) start(); else audio.pause();
  }
  function seek(t) {
    audio.currentTime = clamp(t, 0, TL.duration - 0.05);
    lastCT = -1;
  }

  audio.addEventListener('play', () => setPlaying(true));
  audio.addEventListener('pause', () => setPlaying(false));
  audio.addEventListener('ended', () => {
    setPlaying(false);
    overlay.hidden = false;
    $('overlay-label').textContent = 'Watch again';
    audio.currentTime = 0;
    poster = TL.duration - 1.0;
  });

  $('bigplay').addEventListener('click', start);
  playBtn.addEventListener('click', toggle);
  canvas.addEventListener('click', toggle);
  scrub.addEventListener('input', () => { dragging = true; seek((+scrub.value / 1000) * TL.duration); });
  scrub.addEventListener('change', () => { dragging = false; });
  ccBtn.addEventListener('click', () => {
    captions = !captions;
    ccBtn.setAttribute('aria-pressed', String(captions));
    try { localStorage.setItem('fleeced-cc', captions ? '1' : '0'); } catch (e) { /* storage unavailable */ }
  });
  try {
    if (localStorage.getItem('fleeced-cc') === '0') { captions = false; ccBtn.setAttribute('aria-pressed', 'false'); }
  } catch (e) { /* storage unavailable */ }
  fsBtn.addEventListener('click', async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await stage.requestFullscreen();
    } catch (e) { fsBtn.disabled = true; fsBtn.title = 'Full screen is not available here'; }
  });
  document.addEventListener('keydown', (ev) => {
    if (ev.target.closest && ev.target.closest('input, button') && ev.key !== ' ') return;
    if (ev.key === ' ' || ev.key === 'k') { ev.preventDefault(); toggle(); }
    else if (ev.key === 'ArrowRight') seek(audio.currentTime + 5);
    else if (ev.key === 'ArrowLeft') seek(audio.currentTime - 5);
    else if (ev.key === 'c') ccBtn.click();
    else if (ev.key === 'f') fsBtn.click();
  });
  new ResizeObserver(resize).observe(canvas);

  ready.then(() => {
    resize();
    document.documentElement.classList.add('fonts-ready');
    requestAnimationFrame(loop);
  });
})();
