'use strict';
/* ============================================================
   Möbius Lab core: router, shared renderer, theme, UI, math.
   ============================================================ */
const Lab = (() => {
  const TAU = Math.PI * 2;
  const chapters = [];
  const byToken = {};
  let active = null;
  let renderer = null;
  let lastT = performance.now();
  const themeSubs = [];

  /* ---------------- theme ---------------- */
  function isDark() {
    const t = document.documentElement.getAttribute('data-theme');
    if (t === 'dark') return true;
    if (t === 'light') return false;
    return window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches;
  }
  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }
  function onTheme(cb) { themeSubs.push(cb); }
  function fireTheme() { const d = isDark(); themeSubs.forEach(cb => { try { cb(d); } catch (e) { console.error(e); } }); }
  if (window.matchMedia) {
    const mq = matchMedia('(prefers-color-scheme: dark)');
    (mq.addEventListener ? mq.addEventListener('change', fireTheme) : mq.addListener(fireTheme));
  }
  new MutationObserver(fireTheme).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  /* ---------------- renderer ---------------- */
  function getRenderer() {
    if (renderer) return renderer;
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.domElement.setAttribute('aria-label', '3D view. Drag to rotate, pinch or scroll to zoom.');
    renderer.domElement.style.touchAction = 'none';  // one finger rotates the view instead of scrolling the page
    return renderer;
  }
  function sizeActive() {
    if (!active || !active.stage) return;
    const r = active.stage.getBoundingClientRect();
    const w = Math.max(1, Math.round(r.width)), h = Math.max(1, Math.round(r.height));
    if (active.gl) {
      getRenderer().setSize(w, h, false);
      if (active.camera) { active.camera.aspect = w / h; active.camera.updateProjectionMatrix(); }
    }
    if (active.resize) active.resize(w, h);
  }
  const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(() => sizeActive()) : null;
  window.addEventListener('resize', sizeActive);

  function loop(t) {
    requestAnimationFrame(loop);
    const dt = Math.min(0.05, Math.max(0, (t - lastT) / 1000));
    lastT = t;
    if (!active || document.hidden) return;
    try {
      if (active.frame) active.frame(dt, t / 1000);
      if (active.gl && active.scene && active.camera) getRenderer().render(active.scene, active.camera);
    } catch (e) { console.error(e); }
  }

  /* ---------------- router ---------------- */
  function register(ch) { chapters.push(ch); byToken[ch.token] = ch; }
  function activate(token, opts = {}) {
    const ch = byToken[token] || chapters[0];
    if (active === ch) return;
    if (active) {
      if (active.leave) active.leave();
      if (active.section) active.section.hidden = true;
      if (active.controls) active.controls.enabled = false;
      if (ro && active.stage) ro.unobserve(active.stage);
    }
    active = ch;
    ch.section = ch.section || document.getElementById('ch-' + ch.token);
    ch.section.hidden = false;
    ch.stage = ch.stage || ch.section.querySelector('[data-stage]');
    if (!ch._inited) {
      ch._inited = true;
      try { if (ch.init) ch.init(ch.section, ch.stage); } catch (e) { console.error('init failed', ch.token, e); }
    }
    if (ch.gl && ch.stage) {
      const r = getRenderer();
      ch.stage.prepend(r.domElement);
      if (ch.camera && ch.controls) ch.controls.enabled = true;
      if (ch.background) r.setClearColor(ch.background(), 1);
    }
    if (ro && ch.stage) ro.observe(ch.stage);
    sizeActive();
    if (ch.enter) ch.enter();
    document.querySelectorAll('.nav a').forEach(a => {
      if (a.dataset.token === ch.token) { a.setAttribute('aria-current', 'page'); if (!opts.noScrollNav) a.scrollIntoView({ block: 'nearest', inline: 'center' }); }
      else a.removeAttribute('aria-current');
    });
    if (opts.scroll) {
      const nav = document.querySelector('.nav');
      const top = nav ? nav.getBoundingClientRect().top + window.scrollY : 0;
      if (window.scrollY > top + 4) window.scrollTo({ top, behavior: 'auto' });
    }
  }
  function tokenFromHash() { return (location.hash || '').replace(/^#/, '').trim(); }
  // Keep the experiment column in view while reading the notes, but only when it fits on screen.
  function updateSticky() {
    document.querySelectorAll('.stage-col').forEach(col => {
      col.classList.toggle('fits', col.offsetHeight < window.innerHeight - 80);
    });
  }
  const stickyRO = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(updateSticky) : null;
  function start() {
    document.querySelectorAll('.stage-col').forEach(col => stickyRO && stickyRO.observe(col));
    window.addEventListener('resize', updateSticky);
    document.querySelectorAll('.nav a').forEach(a => {
      a.addEventListener('click', ev => {
        ev.preventDefault();
        const tk = a.dataset.token;
        try { history.replaceState(null, '', '#' + tk); } catch (e) { /* sandboxed */ }
        activate(tk, { scroll: true });
      });
    });
    window.addEventListener('hashchange', () => activate(tokenFromHash(), { scroll: true }));
    document.addEventListener('click', ev => {
      const a = ev.target.closest('a[data-goto]');
      if (!a) return;
      ev.preventDefault();
      try { history.replaceState(null, '', '#' + a.dataset.goto); } catch (e) { /* sandboxed */ }
      activate(a.dataset.goto, { scroll: true });
    });
    const tk = tokenFromHash();
    activate(byToken[tk] ? tk : chapters[0].token, { noScrollNav: true });
    onTheme(() => {
      if (active && active.gl && active.background) getRenderer().setClearColor(active.background(), 1);
    });
    requestAnimationFrame(loop);
  }

  /* ---------------- UI helpers ---------------- */
  function el(tag, attrs = {}, kids = []) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null) continue;
      if (k === 'class') e.className = v;
      else if (k === 'text') e.textContent = v;
      else if (k === 'html') e.innerHTML = v;
      else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v);
    }
    (Array.isArray(kids) ? kids : [kids]).forEach(c => c != null && e.append(c));
    return e;
  }
  const ui = {
    group(parent, label, id) {
      const g = el('div', { class: 'ctl' });
      if (label) g.append(el('span', { class: 'lbl', id: id ? id + '-lbl' : null, text: label }));
      parent.append(g);
      return g;
    },
    seg(parent, { label, options, value, onChange, id }) {
      const g = ui.group(parent, label, id);
      const wrap = el('div', { class: 'seg', role: 'group', 'aria-label': label || '' });
      const btns = options.map(o => {
        const b = el('button', { type: 'button', id: id ? `${id}-${o.value}` : null, 'aria-pressed': String(o.value === value), text: o.label, title: o.title || null });
        b.addEventListener('click', () => { api.set(o.value); onChange && onChange(o.value); });
        wrap.append(b);
        return b;
      });
      g.append(wrap);
      const api = {
        el: g, value,
        set(v) { api.value = v; btns.forEach((b, i) => b.setAttribute('aria-pressed', String(options[i].value === v))); },
        get() { return api.value; }
      };
      return api;
    },
    slider(parent, { label, min, max, step, value, format, onInput, id }) {
      const g = ui.group(parent, label, id);
      const row = el('div', { class: 'range' });
      const inp = el('input', { type: 'range', min, max, step, value, id: id || null, 'aria-label': label || '' });
      const out = el('output', { for: id || null });
      const fmtv = v => (format ? format(+v) : String(v));
      out.textContent = fmtv(value);
      inp.addEventListener('input', () => { out.textContent = fmtv(inp.value); onInput && onInput(+inp.value); });
      row.append(inp, out);
      g.append(row);
      return { el: g, input: inp, set(v) { inp.value = v; out.textContent = fmtv(v); }, get: () => +inp.value };
    },
    button(parent, { label, onClick, primary, id, title }) {
      const b = el('button', { type: 'button', class: 'btn' + (primary ? ' primary' : ''), id: id || null, text: label, title: title || null });
      b.addEventListener('click', onClick);
      parent.append(b);
      return b;
    },
    chips(parent, { label, options, values, onChange, id }) {
      const g = ui.group(parent, label, id);
      const wrap = el('div', { class: 'chips', role: 'group', 'aria-label': label || '' });
      const set = new Set(values || []);
      const btns = options.map(o => {
        const b = el('button', { type: 'button', id: id ? `${id}-${String(o.value).replace(/[^a-z0-9]/gi, '_')}` : null, 'aria-pressed': String(set.has(o.value)), text: o.label });
        b.addEventListener('click', () => {
          if (set.has(o.value)) set.delete(o.value); else set.add(o.value);
          b.setAttribute('aria-pressed', String(set.has(o.value)));
          onChange && onChange([...set]);
        });
        wrap.append(b);
        return b;
      });
      g.append(wrap);
      return {
        el: g,
        get: () => [...set],
        set(vals) { set.clear(); vals.forEach(v => set.add(v)); btns.forEach((b, i) => b.setAttribute('aria-pressed', String(set.has(options[i].value)))); }
      };
    },
    row(parent) { const r = el('div', { class: 'btn-row' }); parent.append(r); return r; }
  };
  function toast(stage, msg, ms = 2600) {
    let t = stage.querySelector('.toast');
    if (!t) { t = el('div', { class: 'toast', role: 'status' }); stage.append(t); }
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(t._h);
    t._h = setTimeout(() => t.classList.remove('show'), ms);
  }
  function fitCanvas(canvas) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = Math.max(1, canvas.clientWidth), h = Math.max(1, canvas.clientHeight);
    if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    }
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, w, h, dpr };
  }

  /* ---------------- textures ---------------- */
  const texCache = {};
  function paperTexture(lined, base = '#f27aa2', key) {
    const k = (key || base) + (lined ? ':L' : ':P');
    if (texCache[k]) return texCache[k];
    const W = 512, H = 128;
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const g = c.getContext('2d');
    g.fillStyle = base; g.fillRect(0, 0, W, H);
    const img = g.getImageData(0, 0, W, H); const d = img.data;
    let seed = 1234567;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    for (let i = 0; i < d.length; i += 4) { const n = (rnd() - 0.5) * 14; d[i] += n; d[i + 1] += n; d[i + 2] += n; }
    g.putImageData(img, 0, 0);
    if (lined) {
      g.strokeStyle = 'rgba(52, 66, 168, 0.72)'; g.lineWidth = 2.4;
      for (let i = 0; i < 4; i++) { const x = (i + 0.5) * W / 4; g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H); g.stroke(); }
    }
    const tex = new THREE.CanvasTexture(c);
    tex.wrapS = THREE.RepeatWrapping; tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.encoding = THREE.sRGBEncoding;
    tex.anisotropy = 4;
    texCache[k] = tex;
    return tex;
  }
  function woodTexture() {
    if (texCache.wood) return texCache.wood;
    const W = 1024, H = 1024;
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const g = c.getContext('2d');
    g.fillStyle = '#b07a4a'; g.fillRect(0, 0, W, H);
    let seed = 99;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    for (let i = 0; i < 260; i++) {
      const y = rnd() * H, amp = 4 + rnd() * 18, ph = rnd() * TAU, f = 0.002 + rnd() * 0.006;
      g.strokeStyle = `rgba(${90 + rnd() * 40 | 0}, ${55 + rnd() * 25 | 0}, ${30 + rnd() * 20 | 0}, ${0.12 + rnd() * 0.22})`;
      g.lineWidth = 0.6 + rnd() * 2.2;
      g.beginPath();
      for (let x = 0; x <= W; x += 16) { const yy = y + Math.sin(x * f * TAU + ph) * amp; x ? g.lineTo(x, yy) : g.moveTo(x, yy); }
      g.stroke();
    }
    const tex = new THREE.CanvasTexture(c);
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    tex.encoding = THREE.sRGBEncoding;
    texCache.wood = tex;
    return tex;
  }

  /* ---------------- band math ---------------- */
  // Core circle radius R, width W, n half-twists, chirality chi (+1/-1), s in [-1,1].
  // a0 stands the strip up: at a0 = pi/2 a plain ring is a cylinder, which is what paper can actually make.
  function bandPoint(theta, s, n, chi, R, W, out = [0, 0, 0], a0 = Math.PI / 2) {
    const a = chi * n * theta / 2 + a0, ca = Math.cos(a), sa = Math.sin(a), ct = Math.cos(theta), st = Math.sin(theta);
    const h = s * W / 2;
    out[0] = (R + h * ca) * ct; out[1] = (R + h * ca) * st; out[2] = h * sa;
    return out;
  }
  function bandFrame(theta, s, n, chi, R, W, a0 = Math.PI / 2) {
    const ap = chi * n / 2, a = ap * theta + a0, ca = Math.cos(a), sa = Math.sin(a), ct = Math.cos(theta), st = Math.sin(theta);
    const h = s * W / 2;
    const p = new THREE.Vector3((R + h * ca) * ct, (R + h * ca) * st, h * sa);
    // dP/dtheta
    const dt = new THREE.Vector3(-(R + h * ca) * st - h * sa * ap * ct, (R + h * ca) * ct - h * sa * ap * st, h * ca * ap);
    // dP/ds  (direction of the ruling)
    const ds = new THREE.Vector3(ca * ct, ca * st, sa);
    const nrm = new THREE.Vector3().crossVectors(dt, ds).normalize();
    return { p, tangent: dt.clone().normalize(), ruling: ds, normal: nrm, speed: dt.length() };
  }
  // Indexed band geometry over phi in [phi0, phi1], s in [s0, s1]. UV u is arc length / tile.
  function bandGeometry({ n = 1, chi = 1, R = 1.2, W = 0.6, segU = 240, segV = 8, s0 = -1, s1 = 1, phi0 = 0, phi1 = TAU, tile = 1 }) {
    const nu = segU + 1, nv = segV + 1;
    const pos = new Float32Array(nu * nv * 3), nor = new Float32Array(nu * nv * 3), uv = new Float32Array(nu * nv * 2);
    const tmp = [0, 0, 0];
    for (let i = 0; i < nu; i++) {
      const phi = phi0 + (phi1 - phi0) * i / segU;
      for (let j = 0; j < nv; j++) {
        const s = s0 + (s1 - s0) * j / segV;
        const k = i * nv + j;
        bandPoint(phi, s, n, chi, R, W, tmp);
        pos[k * 3] = tmp[0]; pos[k * 3 + 1] = tmp[1]; pos[k * 3 + 2] = tmp[2];
        const f = bandFrame(phi, s, n, chi, R, W);
        nor[k * 3] = f.normal.x; nor[k * 3 + 1] = f.normal.y; nor[k * 3 + 2] = f.normal.z;
        uv[k * 2] = (R * (phi - phi0)) / tile; uv[k * 2 + 1] = (s - s0) / (s1 - s0 || 1);
      }
    }
    const idx = [];
    for (let i = 0; i < segU; i++) for (let j = 0; j < segV; j++) {
      const a = i * nv + j, b = (i + 1) * nv + j, c = (i + 1) * nv + j + 1, d = i * nv + j + 1;
      idx.push(a, b, d, b, c, d);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
    g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    g.setIndex(idx);
    g.userData = { nu, nv, segU, segV };
    return g;
  }

  /* ---------------- 3D scene helpers ---------------- */
  function makeScene({ fov = 40, pos = [2.6, -3.2, 2.3], target = [0, 0, 0], near = 0.05, far = 100 } = {}) {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(fov, 1, near, far);
    camera.up.set(0, 0, 1);
    camera.position.set(...pos);
    camera.lookAt(...target);
    const hemi = new THREE.HemisphereLight(0xffffff, 0x7d83a8, 0.62);
    hemi.position.set(0, 0, 1);
    scene.add(hemi);
    const key = new THREE.DirectionalLight(0xffffff, 0.68);
    key.position.set(3, -4, 6);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0xffffff, 0.3);
    fill.position.set(-4, 3, -2);
    scene.add(fill);
    const controls = new THREE.OrbitControls(camera, getRenderer().domElement);
    controls.target.set(...target);
    controls.enableDamping = true;
    controls.dampingFactor = 0.12;
    controls.enablePan = false;
    controls.rotateSpeed = 0.7;
    controls.minDistance = 1.2;
    controls.maxDistance = 14;
    controls.enabled = false;
    controls.update();
    return { scene, camera, controls };
  }
  function stageBg() { return new THREE.Color(cssVar('--stage') || '#e6eaf4'); }
  // Animate camera to a pose.
  function tweenCamera(ch, pos, target, dur = 0.9) {
    ch._tween = { t: 0, dur, p0: ch.camera.position.clone(), p1: new THREE.Vector3(...pos), q0: ch.controls.target.clone(), q1: new THREE.Vector3(...target) };
  }
  function stepTween(ch, dt) {
    const tw = ch._tween; if (!tw) return false;
    tw.t = Math.min(1, tw.t + dt / tw.dur);
    const e = tw.t < 0.5 ? 2 * tw.t * tw.t : 1 - Math.pow(-2 * tw.t + 2, 2) / 2;
    ch.camera.position.lerpVectors(tw.p0, tw.p1, e);
    ch.controls.target.lerpVectors(tw.q0, tw.q1, e);
    ch.camera.lookAt(ch.controls.target);
    if (tw.t >= 1) ch._tween = null;
    return true;
  }
  // Replace vertex-colour multiply with a paint mix: colour.r = paint amount.
  function paintMaterial(map, paint = '#1aa9c9', side = THREE.FrontSide) {
    const m = new THREE.MeshStandardMaterial({ map, roughness: 0.88, metalness: 0, side, vertexColors: true });
    const pc = new THREE.Color(paint);
    m.onBeforeCompile = sh => {
      sh.uniforms.uPaint = { value: pc };
      sh.fragmentShader = 'uniform vec3 uPaint;\n' + sh.fragmentShader.replace('#include <color_fragment>',
        '#ifdef USE_COLOR\n diffuseColor.rgb = mix(diffuseColor.rgb, uPaint, clamp(vColor.r, 0.0, 1.0) * 0.82);\n#endif');
    };
    m.userData.paint = pc;
    return m;
  }

  /* ---------------- topology (exact for polygons) ---------------- */
  const ROT = (() => {
    const a = 0.3123, b = 0.1777, ca = Math.cos(a), sa = Math.sin(a), cb = Math.cos(b), sb = Math.sin(b);
    return p => { const x = p[0], y = p[1], z = p[2]; const y1 = y * ca - z * sa, z1 = y * sa + z * ca; return [x * cb + z1 * sb, y1, -x * sb + z1 * cb]; };
  })();
  function segInter(p1, p2, q1, q2) {
    const rx = p2[0] - p1[0], ry = p2[1] - p1[1], sx = q2[0] - q1[0], sy = q2[1] - q1[1];
    const den = rx * sy - ry * sx; if (Math.abs(den) < 1e-14) return null;
    const qpx = q1[0] - p1[0], qpy = q1[1] - p1[1];
    const t = (qpx * sy - qpy * sx) / den, u = (qpx * ry - qpy * rx) / den;
    if (t < 0 || t >= 1 || u < 0 || u >= 1) return null;
    return { t, u, sign: Math.sign(den) };
  }
  function bbox2(P) { let a = Infinity, b = Infinity, c = -Infinity, d = -Infinity; for (const p of P) { if (p[0] < a) a = p[0]; if (p[1] < b) b = p[1]; if (p[0] > c) c = p[0]; if (p[1] > d) d = p[1]; } return [a, b, c, d]; }
  // Uniform 2D grid over segments, so crossing searches are not all-pairs.
  function segGrid(P, cell, box) {
    const [x0, y0] = box, nx = Math.max(1, Math.ceil((box[2] - x0) / cell) + 1), ny = Math.max(1, Math.ceil((box[3] - y0) / cell) + 1);
    const buckets = new Map();
    const N = P.length;
    for (let i = 0; i < N; i++) {
      const p1 = P[i], p2 = P[(i + 1) % N];
      const ix0 = Math.floor((Math.min(p1[0], p2[0]) - x0) / cell), ix1 = Math.floor((Math.max(p1[0], p2[0]) - x0) / cell);
      const iy0 = Math.floor((Math.min(p1[1], p2[1]) - y0) / cell), iy1 = Math.floor((Math.max(p1[1], p2[1]) - y0) / cell);
      for (let ix = ix0; ix <= ix1; ix++) for (let iy = iy0; iy <= iy1; iy++) {
        const k = ix * ny + iy; let b = buckets.get(k); if (!b) buckets.set(k, b = []); b.push(i);
      }
    }
    return { buckets, nx, ny, x0, y0, cell };
  }
  function gridQuery(G, p1, p2, cb) {
    const { x0, y0, cell, ny } = G;
    const ix0 = Math.floor((Math.min(p1[0], p2[0]) - x0) / cell), ix1 = Math.floor((Math.max(p1[0], p2[0]) - x0) / cell);
    const iy0 = Math.floor((Math.min(p1[1], p2[1]) - y0) / cell), iy1 = Math.floor((Math.max(p1[1], p2[1]) - y0) / cell);
    for (let ix = ix0; ix <= ix1; ix++) for (let iy = iy0; iy <= iy1; iy++) { const b = G.buckets.get(ix * ny + iy); if (b) for (const j of b) cb(j); }
  }
  function meanSeg(P) { let s = 0; for (let i = 0; i < P.length; i++) { const a = P[i], b = P[(i + 1) % P.length]; s += Math.hypot(b[0] - a[0], b[1] - a[1]); } return s / P.length; }
  // Linking number of two closed polylines (arrays of [x,y,z]); positive = right-handed.
  function linking(A, B) {
    A = A.map(ROT); B = B.map(ROT);
    const bb = bbox2(A.concat(B)), cell = Math.max(1e-6, 2 * Math.max(meanSeg(A), meanSeg(B)));
    const G = segGrid(B, cell, bb), seen = new Int32Array(B.length).fill(-1);
    let sum = 0;
    for (let i = 0; i < A.length; i++) {
      const a1 = A[i], a2 = A[(i + 1) % A.length];
      gridQuery(G, a1, a2, j => {
        if (seen[j] === i) return; seen[j] = i;
        const b1 = B[j], b2 = B[(j + 1) % B.length];
        const r = segInter(a1, a2, b1, b2); if (!r) return;
        const za = a1[2] + r.t * (a2[2] - a1[2]), zb = b1[2] + r.u * (b2[2] - b1[2]);
        sum += za > zb ? r.sign : -r.sign;
      });
    }
    return Math.round(sum / 2);
  }
  function bareissDet(M) {
    const n = M.length; if (n === 0) return 1n;
    const A = M.map(r => r.map(v => BigInt(v))); let prev = 1n, sign = 1n;
    for (let k = 0; k < n - 1; k++) {
      if (A[k][k] === 0n) {
        let sw = -1; for (let i = k + 1; i < n; i++) if (A[i][k] !== 0n) { sw = i; break; }
        if (sw < 0) return 0n;
        [A[k], A[sw]] = [A[sw], A[k]]; sign = -sign;
      }
      for (let i = k + 1; i < n; i++) for (let j = k + 1; j < n; j++) A[i][j] = (A[i][j] * A[k][k] - A[i][k] * A[k][j]) / prev;
      prev = A[k][k];
    }
    return sign * A[n - 1][n - 1];
  }
  // Knot determinant |Δ(-1)| of a closed polyline: 1 unknot, 3 trefoil, 5 cinquefoil or figure-eight ...
  function knotDet(P) {
    P = P.map(ROT); const N = P.length; const events = []; let cid = 0;
    const G = segGrid(P, Math.max(1e-6, 2 * meanSeg(P)), bbox2(P)), seen = new Int32Array(N).fill(-1);
    for (let i = 0; i < N; i++) {
      const p1 = P[i], p2 = P[(i + 1) % N];
      gridQuery(G, p1, p2, j => {
        if (j < i + 2 || seen[j] === i) return; seen[j] = i;
        if (i === 0 && j === N - 1) return;
        const q1 = P[j], q2 = P[(j + 1) % N];
        const r = segInter(p1, p2, q1, q2); if (!r) return;
        const zi = p1[2] + r.t * (p2[2] - p1[2]), zj = q1[2] + r.u * (q2[2] - q1[2]);
        events.push({ pos: i + r.t, id: cid, over: zi >= zj }); events.push({ pos: j + r.u, id: cid, over: zj > zi }); cid++;
      });
    }
    const c = cid; if (c === 0) return 1;
    events.sort((a, b) => a.pos - b.pos);
    const unders = events.filter(e => !e.over);
    const overPos = {}; events.forEach(e => { if (e.over) overPos[e.id] = e.pos; });
    const arcOf = pos => { let lo = 0, hi = unders.length - 1, k = -1; while (lo <= hi) { const m = (lo + hi) >> 1; if (unders[m].pos <= pos) { k = m; lo = m + 1; } else hi = m - 1; } return (k + unders.length) % unders.length; };
    const M = Array.from({ length: c }, () => new Array(c).fill(0));
    unders.forEach((u, k) => { const o = arcOf(overPos[u.id]); const row = u.id; M[row][o] += 2; M[row][(k - 1 + c) % c] -= 1; M[row][k] -= 1; });
    const d = bareissDet(M.slice(1).map(r => r.slice(1)));
    return Number(d < 0n ? -d : d);
  }
  function knotName(det) {
    return ({ 1: 'no knot', 3: 'trefoil knot', 5: 'cinquefoil knot', 7: '7-crossing torus knot', 9: '9-crossing torus knot', 11: '11-crossing torus knot' })[det] || `knotted (det ${det})`;
  }

  /* ---------------- misc ---------------- */
  function rng(seed = 1) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function gauss(r) { let u = 0, v = 0; while (u === 0) u = r(); while (v === 0) v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(TAU * v); }
  const fmt = (x, d = 2) => (Number.isFinite(x) ? x.toFixed(d) : '–');
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, t) => a + (b - a) * t;
  const smooth = t => t * t * (3 - 2 * t);

  return {
    TAU, register, start, activate, isDark, cssVar, onTheme, getRenderer, el, ui, toast, fitCanvas,
    paperTexture, woodTexture, bandPoint, bandFrame, bandGeometry, makeScene, stageBg, tweenCamera, stepTween, paintMaterial,
    linking, knotDet, knotName, rng, gauss, fmt, clamp, lerp, smooth, get active() { return active; }
  };
})();
