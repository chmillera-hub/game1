// Deterministic frame renderer: window.renderAt(t) draws the video frame at time t (seconds).
(function () {
  const W = 1080, H = 1920;
  const E = {};
  window.E = E;

  // Shared gradients referenced by rigs/sets (halo, candle and lantern glows).
  E.sharedDefs = `<defs>
    <radialGradient id="haloGlow"><stop offset="0.55" stop-color="#ffe9a8" stop-opacity="0.6"/><stop offset="1" stop-color="#ffe9a8" stop-opacity="0"/></radialGradient>
    <radialGradient id="candleGlow"><stop offset="0" stop-color="#ffd27a" stop-opacity="0.55"/><stop offset="0.4" stop-color="#ffb347" stop-opacity="0.18"/><stop offset="1" stop-color="#ffb347" stop-opacity="0"/></radialGradient>
    <radialGradient id="lanternGlow"><stop offset="0" stop-color="#ffd27a" stop-opacity="0.75"/><stop offset="1" stop-color="#ffb347" stop-opacity="0"/></radialGradient>
    <radialGradient id="warmGlow"><stop offset="0" stop-color="#ffc070" stop-opacity="0.85"/><stop offset="0.35" stop-color="#ff9a40" stop-opacity="0.3"/><stop offset="1" stop-color="#ff8a30" stop-opacity="0"/></radialGradient>
    <radialGradient id="moonGlow"><stop offset="0.25" stop-color="#e8f0ff" stop-opacity="0.55"/><stop offset="1" stop-color="#9fb8ff" stop-opacity="0"/></radialGradient>
    <radialGradient id="whiteGlow"><stop offset="0" stop-color="#ffffff" stop-opacity="0.95"/><stop offset="0.4" stop-color="#fff6dc" stop-opacity="0.45"/><stop offset="1" stop-color="#fff2c8" stop-opacity="0"/></radialGradient>
  </defs>`;

  let TL = null;
  const stage = document.getElementById('stage');
  const slots = [mkSlot('slotA'), mkSlot('slotB')];
  const dust = document.getElementById('dust');
  const dctx = dust.getContext('2d');

  function mkSlot(id) {
    const el = document.createElement('div');
    el.className = 'slot';
    el.id = id;
    stage.insertBefore(el, document.getElementById('dust'));
    return { el, key: null, layers: {} };
  }

  function shotKey(s) { return `${s.id}#${s.take}`; }

  // Transition into shot i: crossfade when the location changes, cut otherwise.
  function transIn(i) {
    if (i === 0) return 0;
    const a = SHOTS[TL.shots[i - 1].id], b = SHOTS[TL.shots[i].id];
    if (b.fadeIn !== undefined) return b.fadeIn;
    return a.set === b.set ? 0 : 0.55;
  }

  function prepare(slot, shot) {
    const key = shotKey(shot);
    if (slot.key === key) return;
    slot.el.innerHTML = '';
    slot.layers = {};
    slot.key = key;
    slot.cache = {};
  }

  function layerEl(slot, L) {
    let el = slot.layers[L.key];
    if (!el) {
      el = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      el.setAttribute('viewBox', `0 0 ${W} ${H}`);
      el.setAttribute('class', 'layer');
      slot.el.appendChild(el);
      slot.layers[L.key] = el;
      el.__svg = null;
      el.__origin = [0, 0];
    }
    return el;
  }

  // Static layers (bake: true) are rasterised once per shot into a canvas, with any blur
  // applied at bake time, so that only cheap transforms remain per frame.
  async function bakeLayer(slot, L) {
    const M = L.margin === undefined ? 0.2 : L.margin;
    const [rx, ry, rw, rh] = (L.region || [-W * M, -H * M, W * (1 + 2 * M), H * (1 + 2 * M)]).map(Math.round);
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${rw}" height="${rh}" viewBox="${rx} ${ry} ${rw} ${rh}">${E.sharedDefs}${L.svg}</svg>`;
    const img = new Image();
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
    await img.decode();
    const cv = document.createElement('canvas');
    cv.width = rw; cv.height = rh;
    const c2 = cv.getContext('2d');
    if (L.blur) c2.filter = `blur(${L.blur}px)`;
    c2.drawImage(img, 0, 0);
    cv.className = 'layer';
    cv.style.width = rw + 'px'; cv.style.height = rh + 'px';
    cv.__origin = [rx, ry];
    slot.el.appendChild(cv);
    slot.layers[L.key] = cv;
    return cv;
  }

  async function drawShot(slot, shot, gt, alpha) {
    prepare(slot, shot);
    const def = SHOTS[shot.id];
    const lt = gt - shot.start;
    const dur = shot.end - shot.start;
    const ctx = { lt, gt, dur, take: shot.take, shot, cache: slot.cache, tl: TL, u: U.clamp(lt / dur) };
    const out = def.draw(ctx);
    const cam = out.camera || { x: 0, y: 0, z: 1 };
    const seen = {};
    for (const [idx, L] of out.layers.entries()) {
      let el;
      if (L.bake) {
        el = slot.layers[L.key] || (await bakeLayer(slot, L));
      } else {
        el = layerEl(slot, L);
        if (el.__svg !== L.svg) { el.innerHTML = L.svg; el.__svg = L.svg; }
        el.style.filter = L.blur ? `blur(${L.blur}px)` : (L.filter || 'none');
      }
      seen[L.key] = true;
      el.style.zIndex = idx;
      const par = L.par === undefined ? 1 : L.par;
      const z = Math.pow(cam.z || 1, par) * (L.scale || 1);
      const tx = -(cam.x || 0) * par + (L.dx || 0), ty = -(cam.y || 0) * par + (L.dy || 0);
      const [ox, oy] = el.__origin;
      let tf = `translate(${W / 2 + tx}px,${H / 2 + ty}px) scale(${z}) translate(${-W / 2}px,${-H / 2}px)`;
      if (L.rot) { const [px, py] = L.pivot || [W / 2, H / 2]; tf += ` translate(${px}px,${py}px) rotate(${L.rot}deg) translate(${-px}px,${-py}px)`; }
      el.style.transform = tf + ` translate(${ox}px,${oy}px)`;
      el.style.transformOrigin = '0 0';
      el.style.opacity = L.opacity === undefined ? 1 : L.opacity;
      el.style.mixBlendMode = (E.noBlend && !(L.blend === 'screen' && !E.noScreen) ? 'normal' : L.blend) || 'normal';
    }
    for (const k in slot.layers) if (!seen[k]) slot.layers[k].style.opacity = 0;
    slot.el.style.opacity = alpha;
    slot.el.style.zIndex = alpha < 1 ? 2 : 1;
    return out;
  }

  // ------------------------------------------------------------- dust motes
  const sprites = {};
  function sprite(col) {
    if (sprites[col]) return sprites[col];
    const c = document.createElement('canvas');
    c.width = c.height = 64;
    const g2 = c.getContext('2d');
    const g = g2.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, `rgba(${col},1)`); g.addColorStop(0.25, `rgba(${col},0.55)`); g.addColorStop(1, `rgba(${col},0)`);
    g2.fillStyle = g; g2.fillRect(0, 0, 64, 64);
    return (sprites[col] = c);
  }
  function drawDust(fx, gt) {
    dctx.clearRect(0, 0, W, H);
    if (!fx || !fx.dust) return;
    const n = fx.dust.n || 40, col = fx.dust.color || '255,236,200';
    const img = sprite(col);
    const r = U.rng(fx.dust.seed || 7);
    for (let i = 0; i < n; i++) {
      const x0 = r() * W, y0 = r() * H, sp = 6 + r() * 16, ph = r() * 100, size = 1.2 + r() * 2.6;
      const x = (x0 + Math.sin(gt * 0.3 + ph) * 30 + gt * sp * (fx.dust.dx || 0.4)) % (W + 40);
      const y = ((y0 - gt * sp * (fx.dust.dy || 1)) % (H + 40) + H + 40) % (H + 40);
      dctx.globalAlpha = (0.25 + 0.75 * Math.abs(Math.sin(gt * 0.8 + ph))) * (fx.dust.alpha || 0.7);
      dctx.drawImage(img, x - size * 3, y - size * 3, size * 6, size * 6);
    }
    dctx.globalAlpha = 1;
  }

  // ------------------------------------------------------------- text overlays
  const subsEl = document.getElementById('subs');
  const secEl = document.getElementById('section');
  const titleEl = document.getElementById('title');
  const endEl = document.getElementById('endcard');
  const vigEl = document.getElementById('vignette');
  const blackEl = document.getElementById('black');

  function env(t, a, b, fi, fo) {
    if (t < a || t > b) return 0;
    return Math.min(1, (t - a) / fi, (b - t) / fo);
  }

  function drawSubs(gt) {
    const s = TL.subs.find((x) => gt >= x.start && gt < x.end);
    if (!s) { subsEl.style.opacity = 0; return; }
    const key = s.unit + s.chunk;
    if (subsEl.__key !== key) {
      const cls = s.who === 'narrator' ? 'narr' : 'speech';
      subsEl.innerHTML = `<div class="${cls}">${s.label ? `<span class="label">${s.label}</span>` : ''}${U.esc(s.text)}</div>`;
      subsEl.__key = key;
    }
    const fin = s.joinPrev ? 1 : (gt - s.start) / 0.09, fout = s.joinNext ? 1 : (s.end - gt) / 0.09;
    subsEl.style.opacity = U.clamp(Math.min(fin, fout));
  }

  function drawSection(gt) {
    const s = TL.sections.find((x) => gt >= x.start && gt < x.end);
    if (!s) { secEl.style.opacity = 0; return; }
    if (secEl.__key !== s.ref) {
      secEl.innerHTML = `<div class="ref">${U.esc(s.ref.toUpperCase())}</div><div class="rule"></div><div class="heading">${U.esc(s.heading)}</div>`;
      secEl.__key = s.ref;
    }
    const a = env(gt, s.start, s.end, 0.7, 0.9);
    secEl.style.opacity = a;
    secEl.style.transform = `translateY(${(1 - a) * 14}px)`;
  }

  function drawTitle(gt) {
    const first = TL.shots[1] ? TL.shots[1].start : 8;
    const a = env(gt, 0.35, first - 0.1, 1.4, 0.8);
    titleEl.style.opacity = a;
    titleEl.style.transform = `scale(${1 + 0.03 * U.clamp(gt / first)})`;
  }

  function drawEnd(gt) {
    const s = TL.shots[TL.shots.length - 1];
    const a = env(gt, s.start + 0.6, TL.duration + 10, 1.4, 1);
    endEl.style.opacity = a;
  }

  // ------------------------------------------------------------- main
  E.load = async function () {
    TL = await (await fetch('build/timeline.json')).json();
    E.TL = TL;
    TL.subs.forEach((x, i) => {
      const p = TL.subs[i - 1], n = TL.subs[i + 1];
      x.joinPrev = !!(p && p.unit === x.unit && Math.abs(p.end - x.start) < 0.05);
      x.joinNext = !!(n && n.unit === x.unit && Math.abs(n.start - x.end) < 0.05);
    });
    endEl.innerHTML = `<div class="endtitle">${U.esc(TL.end.title)}</div><div class="endref">${U.esc(TL.end.ref)}</div>` +
      `<div class="copyright">${U.esc(TL.copyright)}</div>`;
    await document.fonts.ready;
  };

  E.mouthAt = function (gt) {
    const f = gt * TL.fps, i = Math.floor(f), k = f - i;
    const m = TL.mouth;
    return (m[i] || 0) * (1 - k) + (m[i + 1] || 0) * k;
  };

  // Slow speech envelope (0..1): mean mouth opening over the last half second.
  E.speechEnv = function (gt) {
    const f = Math.floor(gt * TL.fps), m = TL.mouth;
    let s = 0;
    for (let i = f - 11; i <= f; i++) s += m[i] || 0;
    return U.clamp(s / 12 * 1.6);
  };

  // Which unit (and how far into it) is being spoken at time t.
  E.unitAt = function (gt) {
    return TL.units.find((u) => gt >= u.start - 0.2 && gt < u.end + 0.2) || null;
  };

  E.renderAt = async function (gt) {
    let i = TL.shots.findIndex((s) => gt >= s.start && gt < s.end);
    if (i < 0) i = gt < 0 ? 0 : TL.shots.length - 1;
    const cur = TL.shots[i];
    const tr = transIn(i);
    let out;
    if (tr > 0 && gt < cur.start + tr && i > 0) {
      const a = U.smooth((gt - cur.start) / tr);
      await drawShot(slots[0], TL.shots[i - 1], gt, 1);
      out = await drawShot(slots[1], cur, gt, a);
    } else {
      // keep the current shot in slot B if it is already there (avoids a rebuild after a fade)
      const useB = slots[1].key === shotKey(cur);
      out = await drawShot(useB ? slots[1] : slots[0], cur, gt, 1);
      (useB ? slots[0] : slots[1]).el.style.opacity = 0;
    }
    drawDust(out.fx, gt);
    vigEl.style.opacity = out.fx && out.fx.vignette !== undefined ? out.fx.vignette : 0.75;
    subsEl.style.top = ((out.fx && out.fx.subY) || 1405) + 'px';
    drawSubs(gt);
    drawSection(gt);
    drawTitle(gt);
    drawEnd(gt);
    const fadeIn = U.clamp(gt / 0.8), fadeOut = U.clamp((TL.duration - gt) / 1.6);
    blackEl.style.opacity = 1 - Math.min(fadeIn, fadeOut);
  };

  // Preview mode: draw one shot at a local time, bypassing the timeline.
  E.renderShot = async function (id, lt, take = 1, dur = 8) {
    const fake = { id, take, start: 0, end: dur };
    const out = await drawShot(slots[0], fake, lt, 1);
    slots[1].el.style.opacity = 0;
    drawDust(out.fx, lt);
    vigEl.style.opacity = out.fx && out.fx.vignette !== undefined ? out.fx.vignette : 0.75;
    subsEl.style.opacity = 0; secEl.style.opacity = 0; titleEl.style.opacity = 0; endEl.style.opacity = 0;
    blackEl.style.opacity = 0;
  };
})();
