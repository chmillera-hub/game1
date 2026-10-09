/* Mobius Lab UI: setup controls, the 3D cutting mat, and the results list. */
(function () {
  'use strict';
  const C = window.MobiusCore;

  const STRIP_COLORS = ['#f4f1e8', '#9fcbe9', '#f2b4c3', '#f3d47a'];
  const PIECE_COLORS = ['#f3d06b', '#7fc0e6', '#ef93aa', '#9fd68a', '#c3a6ee', '#f4a465', '#7fd6c8', '#e7e2d6'];
  const QUICK_CUTS = [
    { label: '½', value: 1 / 2 },
    { label: '⅓', value: 1 / 3 },
    { label: '¼', value: 1 / 4 },
    { label: '⅕', value: 1 / 5 },
  ];
  const PRESETS = [
    { name: 'Möbius strip, cut down the middle', strips: [[1, [1 / 2]]] },
    { name: 'Möbius strip, cut a third of the way in', strips: [[1, [1 / 3]]] },
    { name: 'Möbius strip, cut a quarter of the way in', strips: [[1, [1 / 4]]] },
    { name: 'Plain loop, cut down the middle', strips: [[0, [1 / 2]]] },
    { name: 'Loop with a full twist, cut down the middle', strips: [[2, [1 / 2]]] },
    { name: 'Three half-twists, cut down the middle', strips: [[3, [1 / 2]]] },
    { name: 'Two plain loops taped crossed, both halved', strips: [[0, [1 / 2]], [0, [1 / 2]]], joints: ['orthogonal'] },
    { name: 'Two Möbius strips, opposite twists, taped crossed, both halved', strips: [[1, [1 / 2]], [-1, [1 / 2]]], joints: ['orthogonal'] },
    { name: 'Two Möbius strips, same twist, taped crossed, both halved', strips: [[1, [1 / 2]], [1, [1 / 2]]], joints: ['orthogonal'] },
    { name: 'Möbius strip and plain loop taped crossed, both halved', strips: [[1, [1 / 2]], [0, [1 / 2]]], joints: ['orthogonal'] },
    { name: 'Two Möbius strips taped crossed, both cut at a third', strips: [[1, [1 / 3]], [-1, [1 / 3]]], joints: ['orthogonal'] },
    { name: 'Two full-twist loops taped crossed, both halved', strips: [[2, [1 / 2]], [2, [1 / 2]]], joints: ['orthogonal'] },
    { name: 'Two Möbius strips taped parallel, both halved', strips: [[1, [1 / 2]], [1, [1 / 2]]], joints: ['parallel'] },
    { name: 'Three Möbius strips taped in a column, all halved', strips: [[1, [1 / 2]], [-1, [1 / 2]], [1, [1 / 2]]], joints: ['orthogonal', 'orthogonal'] },
  ];
  const DEFAULT_PRESET = 1;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = (id) => document.getElementById(id);

  const state = {
    config: presetConfig(PRESETS[DEFAULT_PRESET]),
    model: null,
    result: null,
    before: null,
    phase: 'setup', // 'setup' | 'cutting' | 'cut'
    view: 'cut', // 'cut' | 'pull'
    sim: null,
    gap: 0.5,
    shownGap: 0,
    edges: true,
    hidden: new Set(),
    focus: -1,
    customDraft: {},
    errors: {},
  };

  function presetConfig(p) {
    return {
      strips: p.strips.map(([k, cuts]) => ({ halfTwists: k, cuts: cuts.slice() })),
      joints: (p.joints || []).slice(),
    };
  }

  // ------------------------------------------------------------ 3D scene --

  const stage = $('stage');
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  stage.prepend(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 0.05, 200);
  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;

  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a9a90, 0.75));
  const sun = new THREE.DirectionalLight(0xffffff, 0.65);
  sun.position.set(4, 9, 6);
  scene.add(sun);
  const fill = new THREE.DirectionalLight(0xffffff, 0.25);
  fill.position.set(-6, 3, -4);
  scene.add(fill);

  const world = new THREE.Group();
  scene.add(world);
  let mat = null;

  // Core works in (x, y, z) with z up; three.js uses y up.
  const toThree = (p) => [p[0], p[2], -p[1]];

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function buildMat() {
    if (mat) { world.remove(mat); mat.geometry.dispose(); mat.material.map.dispose(); mat.material.dispose(); }
    const size = 16;
    const px = 1024;
    const cv = document.createElement('canvas');
    cv.width = cv.height = px;
    const g = cv.getContext('2d');
    g.fillStyle = cssVar('--mat') || '#2c5a4b';
    g.fillRect(0, 0, px, px);
    const line = cssVar('--mat-line') || '#6f9c8b';
    const step = px / (size * 4);
    g.strokeStyle = line;
    for (let i = 0; i <= size * 4; i++) {
      const major = i % 4 === 0;
      g.globalAlpha = major ? 0.75 : 0.28;
      g.lineWidth = major ? 2 : 1;
      g.beginPath(); g.moveTo(i * step, 0); g.lineTo(i * step, px); g.stroke();
      g.beginPath(); g.moveTo(0, i * step); g.lineTo(px, i * step); g.stroke();
    }
    g.globalAlpha = 0.35;
    g.lineWidth = 1.5;
    for (const k of [-1, 0, 1]) { // the 45° guide lines every cutting mat has
      g.beginPath(); g.moveTo(px * k, 0); g.lineTo(px * (k + 1), px); g.stroke();
      g.beginPath(); g.moveTo(px * (k + 1), 0); g.lineTo(px * k, px); g.stroke();
    }
    g.globalAlpha = 0.85;
    g.fillStyle = cssVar('--mat-ink') || '#e7efe9';
    g.font = '600 15px ' + (cssVar('--font-mono') || 'monospace');
    for (let i = 1; i < size; i++) g.fillText(String(i), i * step * 4 + 4, 18);
    const tex = new THREE.CanvasTexture(cv);
    tex.anisotropy = 4;
    mat = new THREE.Mesh(new THREE.PlaneGeometry(size, size), new THREE.MeshLambertMaterial({ map: tex }));
    mat.rotation.x = -Math.PI / 2;
    world.add(mat);
    placeMat();
    renderer.setClearColor(new THREE.Color(cssVar('--mat') || '#2c5a4b'));
  }

  function placeMat() {
    if (!mat || !state.model) return;
    mat.position.y = state.model.bounds.min[2] - 0.45;
  }

  // Paper surface. Normals are matched per face so one-sided pieces shade
  // smoothly instead of going dark where the paper meets its own back.
  function paperGeometry(getPos, faces, faceColor) {
    const n = faces.length;
    const pos = new Float32Array(n * 18);
    const nor = new Float32Array(n * 18);
    const col = new Float32Array(n * 18);
    const fn = new Float32Array(n * 3);
    const vn = new Map();
    const tmp = new THREE.Color();
    faces.forEach((f, i) => {
      const a = getPos(f[0]), b = getPos(f[1]), c = getPos(f[2]), d = getPos(f[3]);
      const ux = c[0] - a[0], uy = c[1] - a[1], uz = c[2] - a[2];
      const vx = d[0] - b[0], vy = d[1] - b[1], vz = d[2] - b[2];
      let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      const len = Math.hypot(nx, ny, nz) || 1;
      nx /= len; ny /= len; nz /= len;
      fn[3 * i] = nx; fn[3 * i + 1] = ny; fn[3 * i + 2] = nz;
      for (const v of f) {
        let acc = vn.get(v);
        if (!acc) vn.set(v, (acc = [0, 0, 0]));
        const s = acc[0] * nx + acc[1] * ny + acc[2] * nz < 0 ? -1 : 1;
        acc[0] += s * nx; acc[1] += s * ny; acc[2] += s * nz;
      }
    });
    let o = 0;
    faces.forEach((f, i) => {
      const nx = fn[3 * i], ny = fn[3 * i + 1], nz = fn[3 * i + 2];
      tmp.set(faceColor(i));
      for (const k of [0, 1, 2, 0, 2, 3]) {
        const v = f[k];
        const p = getPos(v);
        const a = vn.get(v);
        const s = a[0] * nx + a[1] * ny + a[2] * nz < 0 ? -1 : 1;
        const l = Math.hypot(a[0], a[1], a[2]) || 1;
        pos[o] = p[0]; pos[o + 1] = p[1]; pos[o + 2] = p[2];
        nor[o] = (s * a[0]) / l; nor[o + 1] = (s * a[1]) / l; nor[o + 2] = (s * a[2]) / l;
        col[o] = tmp.r; col[o + 1] = tmp.g; col[o + 2] = tmp.b;
        o += 3;
      }
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
    return geo;
  }

  function paperMaterial(opacity) {
    return new THREE.MeshStandardMaterial({
      vertexColors: true, side: THREE.DoubleSide, roughness: 0.9, metalness: 0,
      polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
      transparent: opacity < 1, opacity, depthWrite: opacity >= 1,
    });
  }

  let layers = []; // objects currently on the mat
  let cutLines = [];
  function clearWorld() {
    for (const o of layers.concat(cutLines)) {
      world.remove(o);
      o.geometry.dispose();
      o.material.dispose();
    }
    for (const { group } of rigidMeshes) {
      world.remove(group);
      group.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); });
    }
    rigidMeshes = [];
    layers = [];
    cutLines = [];
  }

  function lineObject(points, color, opts) {
    const arr = new Float32Array(points.length * 3);
    points.forEach((p, i) => { const q = toThree(p); arr.set(q, i * 3); });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(arr, 3));
    const matl = opts && opts.dashed
      ? new THREE.LineDashedMaterial({ color, dashSize: 0.09, gapSize: 0.05 })
      : new THREE.LineBasicMaterial({ color, transparent: true, opacity: (opts && opts.opacity) || 1 });
    const obj = opts && opts.loop ? new THREE.LineLoop(geo, matl) : new THREE.Line(geo, matl);
    if (opts && opts.dashed) obj.computeLineDistances();
    return obj;
  }

  // Paper stays light in both themes, so its edges are always drawn dark.
  const inkColor = () => new THREE.Color('#1f2b26');

  // Uncut paper with the planned cut lines drawn on it.
  function drawUncut(progress) {
    clearWorld();
    const m = state.model;
    const P = m.positions.map(toThree);
    const geo = paperGeometry((v) => P[v], m.faces, (i) => STRIP_COLORS[m.faceStrip[i] % STRIP_COLORS.length]);
    const mesh = new THREE.Mesh(geo, paperMaterial(1));
    world.add(mesh);
    layers.push(mesh);
    if (state.edges && state.before) {
      const r = state.before;
      for (const piece of r.pieces) for (const L of piece.loops) {
        const obj = lineObject(L.map((v) => r.basePos[v]), inkColor(), { loop: true, opacity: 0.55 });
        world.add(obj);
        layers.push(obj);
      }
    }
    const red = new THREE.Color(cssVar('--cut') || '#cf3e2a');
    for (const path of m.cutPaths) {
      const obj = lineObject(path.points, red, { dashed: progress === undefined });
      if (progress !== undefined) obj.geometry.setDrawRange(0, Math.max(2, Math.floor(progress * path.points.length)));
      world.add(obj);
      cutLines.push(obj);
    }
  }

  // Cut pieces, each its own colour, with the cuts spread open by `gap`.
  function drawPieces(gap) {
    clearWorld();
    const r = state.result;
    const amt = gap * 0.2 * C.WIDTH;
    const P = r.basePos.map((p, v) => toThree([
      p[0] + amt * r.offsets[3 * v], p[1] + amt * r.offsets[3 * v + 1], p[2] + amt * r.offsets[3 * v + 2],
    ]));
    r.pieces.forEach((piece, i) => {
      if (state.hidden.has(i)) return;
      const dim = state.focus >= 0 && state.focus !== i;
      const faces = piece.faceIds.map((fi) => r.faces[fi]);
      const color = PIECE_COLORS[i % PIECE_COLORS.length];
      const mesh = new THREE.Mesh(paperGeometry((v) => P[v], faces, () => color), paperMaterial(dim ? 0.12 : 1));
      if (dim) mesh.renderOrder = 2;
      world.add(mesh);
      layers.push(mesh);
      if (state.edges && !dim) {
        for (const L of piece.loops) {
          const pts = L.map((v) => P[v]);
          const arr = new Float32Array(pts.length * 3);
          pts.forEach((q, k) => arr.set(q, k * 3));
          const g = new THREE.BufferGeometry();
          g.setAttribute('position', new THREE.BufferAttribute(arr, 3));
          const obj = new THREE.LineLoop(g, new THREE.LineBasicMaterial({ color: inkColor(), transparent: true, opacity: 0.6 }));
          world.add(obj);
          layers.push(obj);
        }
      }
    });
    state.shownGap = gap;
  }

  // Pulled-apart view: loops are drawn as ribbons along the physics ropes,
  // other pieces move as they are.
  let rigidMeshes = [];
  function drawPulled(rebuildAll) {
    const sim = state.sim, r = state.result;
    if (rebuildAll) {
      clearWorld();
      rigidMeshes = [];
      sim.bodies.forEach((b, bi) => {
        if (b.kind !== 'rigid' || state.hidden.has(bi)) return;
        const piece = r.pieces[bi];
        const P = r.basePos.map(toThree);
        const color = PIECE_COLORS[bi % PIECE_COLORS.length];
        const group = new THREE.Group();
        const dim = state.focus >= 0 && state.focus !== bi;
        group.add(new THREE.Mesh(paperGeometry((v) => P[v], piece.faceIds.map((fi) => r.faces[fi]), () => color), paperMaterial(dim ? 0.12 : 1)));
        if (state.edges && !dim) for (const L of piece.loops) group.add(lineObject(L.map((v) => r.basePos[v]), inkColor(), { loop: true, opacity: 0.6 }));
        world.add(group);
        rigidMeshes.push({ group, body: b });
      });
    }
    for (const o of layers) { world.remove(o); o.geometry.dispose(); o.material.dispose(); }
    layers = [];
    for (const { group, body } of rigidMeshes) group.position.set(...toThree(body.offset));
    const half = 0.45 * sim.thickness;
    sim.bodies.forEach((b, bi) => {
      if (b.kind !== 'rope' || state.hidden.has(bi)) return;
      const { W, flipped } = C.ribbonFrame(b.X, b.halfTwists);
      const N = b.N;
      const V = [];
      for (let i = 0; i < N; i++) {
        const x = b.X[i], w = W[i];
        V.push(toThree([x[0] + half * w[0], x[1] + half * w[1], x[2] + half * w[2]]));
        V.push(toThree([x[0] - half * w[0], x[1] - half * w[1], x[2] - half * w[2]]));
      }
      const faces = [];
      for (let i = 0; i < N; i++) {
        const j = (i + 1) % N;
        const swap = j === 0 && flipped;
        faces.push([2 * i, swap ? 2 * j + 1 : 2 * j, swap ? 2 * j : 2 * j + 1, 2 * i + 1]);
      }
      const dim = state.focus >= 0 && state.focus !== bi;
      const color = PIECE_COLORS[bi % PIECE_COLORS.length];
      const mesh = new THREE.Mesh(paperGeometry((v) => V[v], faces, () => color), paperMaterial(dim ? 0.12 : 1));
      world.add(mesh);
      layers.push(mesh);
      if (state.edges && !dim) {
        const sides = flipped
          ? [V.filter((_, k) => k % 2 === 0).concat(V.filter((_, k) => k % 2 === 1))]
          : [V.filter((_, k) => k % 2 === 0), V.filter((_, k) => k % 2 === 1)];
        for (const pts of sides) {
          const arr = new Float32Array(pts.length * 3);
          pts.forEach((q, k) => arr.set(q, k * 3));
          const g = new THREE.BufferGeometry();
          g.setAttribute('position', new THREE.BufferAttribute(arr, 3));
          const obj = new THREE.LineLoop(g, new THREE.LineBasicMaterial({ color: inkColor(), transparent: true, opacity: 0.6 }));
          world.add(obj);
          layers.push(obj);
        }
      }
    });
  }

  // Keep the moving pieces in view without taking the camera away from the user.
  function followPulled() {
    const sim = state.sim;
    const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
    sim.bodies.forEach((b) => {
      const pts = b.kind === 'rope' ? b.X : b.P0;
      const o = b.kind === 'rope' ? [0, 0, 0] : b.offset;
      for (let i = 0; i < pts.length; i += 3) for (let k = 0; k < 3; k++) {
        const v = pts[i][k] + o[k];
        if (v < min[k]) min[k] = v;
        if (v > max[k]) max[k] = v;
      }
    });
    const c = toThree([(min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2]);
    const radius = Math.hypot(max[0] - min[0], max[1] - min[1], max[2] - min[2]) / 2;
    const t = controls.target;
    const d = [(c[0] - t.x) * 0.04, (c[1] - t.y) * 0.04, (c[2] - t.z) * 0.04];
    t.x += d[0]; t.y += d[1]; t.z += d[2];
    camera.position.x += d[0]; camera.position.y += d[1]; camera.position.z += d[2];
    const want = radius * 2.9 + 2;
    const off = camera.position.clone().sub(t);
    const dist = off.length();
    if (dist < want) camera.position.copy(t).add(off.multiplyScalar(1 + Math.min(0.02, (want - dist) / dist)));
    if (camera.far < want * 6) { camera.far = want * 6; camera.updateProjectionMatrix(); }
    if (mat) mat.position.y += (min[2] - 0.45 - mat.position.y) * 0.05;
  }

  function startPull() {
    state.view = 'pull';
    state.sim = C.createPullSim(state.result);
    drawPulled(true);
    renderSetup();
    renderResults();
  }

  function stopPull() {
    state.view = 'cut';
    state.sim = null;
    rigidMeshes = [];
    placeMat();
    if (state.phase === 'cut') { drawPieces(state.gap); frameView(); }
    renderSetup();
    renderResults();
  }

  function redraw() {
    if (state.view === 'pull' && state.sim) drawPulled(true);
    else if (state.phase === 'cut') drawPieces(state.gap);
    else drawUncut();
  }

  function frameView() {
    const b = state.model.bounds;
    const lo = toThree(b.min), hi = toThree(b.max);
    const cx = (b.min[0] + b.max[0]) / 2, cy = (lo[1] + hi[1]) / 2, cz = (lo[2] + hi[2]) / 2;
    const span = Math.max(b.max[0] - b.min[0], b.max[1] - b.min[1], b.max[2] - b.min[2]);
    const dist = span * 1.55 + 2.2;
    controls.target.set(cx, cy, cz);
    camera.position.set(cx + dist * 0.62, cy + dist * 0.38, cz + dist * 0.7);
    camera.near = 0.05; camera.far = dist * 10;
    camera.updateProjectionMatrix();
    controls.update();
  }

  function resize() {
    const w = stage.clientWidth, h = stage.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(stage);

  let anim = null;
  function loop(t) {
    if (anim) anim(t);
    if (state.view === 'pull' && state.sim && !state.sim.done) {
      const sim = state.sim;
      const t0 = performance.now();
      do sim.step(1); while (!sim.done && performance.now() - t0 < 9);
      drawPulled(false);
      followPulled();
      if (sim.done || sim.iteration % 60 < 3) renderResults();
      if (sim.done) renderSetup();
    } else if (state.view === 'pull' && state.sim) {
      followPulled();
    }
    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(loop);
  }

  // --------------------------------------------------------- experiment --

  function rebuild(keepView) {
    state.model = C.buildModel(state.config);
    state.config = state.model.config;
    const uncut = { strips: state.config.strips.map((s) => ({ halfTwists: s.halfTwists, cuts: [] })), joints: state.config.joints };
    state.before = C.cutModel(C.buildModel(uncut));
    state.result = null;
    state.phase = 'setup';
    state.view = 'cut';
    state.sim = null;
    state.hidden.clear();
    state.focus = -1;
    anim = null;
    placeMat();
    drawUncut();
    if (!keepView) frameView();
    renderSetup();
    renderResults();
  }

  function doCut(animate) {
    if (!state.model.cutPaths.length) return;
    state.result = C.cutModel(state.model);
    state.hidden.clear();
    state.focus = -1;
    if (!animate || reduceMotion) {
      state.phase = 'cut';
      drawPieces(state.gap);
      renderResults();
      renderSetup();
      return;
    }
    state.phase = 'cutting';
    renderSetup();
    renderResults();
    let start = null;
    const traceMs = 1100, openMs = 650;
    let drew = false;
    anim = (t) => {
      if (start === null) start = t;
      const e = t - start;
      if (e < traceMs) {
        const k = e / traceMs;
        const m = state.model;
        cutLines.forEach((obj, i) => obj.geometry.setDrawRange(0, Math.max(2, Math.floor(k * m.cutPaths[i].points.length))));
        if (!drew) { drawUncut(0); drew = true; }
        return;
      }
      const k = Math.min(1, (e - traceMs) / openMs);
      const ease = 1 - Math.pow(1 - k, 3);
      if (state.phase !== 'cut') { state.phase = 'cut'; renderResults(); renderSetup(); }
      drawPieces(state.gap * ease);
      if (k >= 1) anim = null;
    };
  }

  // ------------------------------------------------------------- setup UI --

  function twistName(k) {
    const hand = k > 0 ? 'right-handed' : 'left-handed';
    if (k === 0) return 'Plain loop, no twist';
    if (Math.abs(k) === 1) return 'Möbius strip, one half-twist, ' + hand;
    if (Math.abs(k) === 2) return 'One full twist, ' + hand + ' (two-sided)';
    const sides = Math.abs(k) % 2 ? 'one-sided' : 'two-sided';
    return Math.abs(k) + ' half-twists, ' + hand + ' (' + sides + ')';
  }

  function fractionLabel(c) {
    for (const q of QUICK_CUTS) if (Math.abs(q.value - c) < 1e-6) return q.label;
    for (let d = 2; d <= 12; d++) {
      const n = Math.round(c * d);
      if (Math.abs(n / d - c) < 1e-6) return n + '/' + d;
    }
    return String(Math.round(c * 1000) / 1000);
  }

  function el(tag, attrs, ...kids) {
    const e = document.createElement(tag);
    for (const k in attrs || {}) {
      if (k === 'class') e.className = attrs[k];
      else if (k.startsWith('on')) e.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] !== undefined && attrs[k] !== null) e.setAttribute(k, attrs[k]);
    }
    for (const kid of kids.flat()) if (kid !== null && kid !== undefined) e.append(kid.nodeType ? kid : document.createTextNode(kid));
    return e;
  }

  function changeConfig(fn) {
    fn(state.config);
    rebuild(true);
  }

  function renderSetup() {
    const box = $('strips');
    const active = document.activeElement && document.activeElement.id;
    box.textContent = '';
    const cfg = state.config;
    cfg.strips.forEach((s, i) => {
      if (i > 0) {
        const j = cfg.joints[i - 1];
        box.append(el('div', { class: 'joint' },
          el('span', { class: 'label' }, 'Tape strip ' + i + ' to strip ' + (i + 1)),
          el('div', { class: 'seg', role: 'group', 'aria-label': 'How strip ' + (i + 1) + ' is taped on' },
            el('button', { type: 'button', id: 'joint-' + i + '-o', 'aria-pressed': String(j === 'orthogonal'), onclick: () => changeConfig((c) => (c.joints[i - 1] = 'orthogonal')) }, 'Orthogonal ⟂'),
            el('button', { type: 'button', id: 'joint-' + i + '-p', 'aria-pressed': String(j === 'parallel'), onclick: () => changeConfig((c) => (c.joints[i - 1] = 'parallel')) }, 'Parallel ∥')),
          el('p', { class: 'note' }, j === 'orthogonal'
            ? 'Crossed at right angles, taped where they overlap in a square.'
            : 'Laid on top of each other running the same way, taped along the overlap.')));
      }
      const odd = Math.abs(s.halfTwists) % 2 === 1;
      const notes = [];
      for (const c of s.cuts) {
        if (odd && Math.abs(c - 0.5) > 1e-6) notes.push('The ' + fractionLabel(c) + ' cut goes around twice and comes back along ' + fractionLabel(1 - c) + ', like real scissors would.');
      }
      const chips = QUICK_CUTS.map((q) => {
        const on = s.cuts.some((c) => Math.abs(c - q.value) < 1e-6);
        return el('button', {
          type: 'button', class: 'chip', id: 'cut-' + i + '-' + q.label, 'aria-pressed': String(on),
          'aria-label': 'Cut at ' + q.label + ' of the width',
          onclick: () => changeConfig((c) => {
            const st = c.strips[i];
            st.cuts = on ? st.cuts.filter((x) => Math.abs(x - q.value) > 1e-6) : st.cuts.concat(q.value);
          }),
        }, q.label);
      });
      const extra = s.cuts.filter((c) => !QUICK_CUTS.some((q) => Math.abs(q.value - c) < 1e-6)).map((cv) =>
        el('button', {
          type: 'button', class: 'chip', 'aria-pressed': 'true', id: 'cut-' + i + '-x' + Math.round(cv * 1000), 'aria-label': 'Remove cut at ' + fractionLabel(cv),
          onclick: () => changeConfig((c) => (c.strips[i].cuts = c.strips[i].cuts.filter((x) => Math.abs(x - cv) > 1e-6))),
        }, fractionLabel(cv) + ' ×'));
      const inputId = 'custom-' + i;
      const addCustom = () => {
        const raw = (document.getElementById(inputId) || {}).value || '';
        const v = C.parseFraction(raw);
        if (v === null || !C.isValidCut(v)) {
          state.errors[i] = 'Type a fraction between 0 and 1, like 2/5 or 0.3.';
          state.customDraft[i] = raw;
          renderSetup();
          return;
        }
        delete state.errors[i];
        state.customDraft[i] = '';
        changeConfig((c) => c.strips[i].cuts.push(v));
      };
      const input = el('input', {
        id: inputId, type: 'text', inputmode: 'decimal', placeholder: 'Other, e.g. 2/5', 'aria-label': 'Custom cut position for strip ' + (i + 1),
        oninput: (e) => (state.customDraft[i] = e.target.value),
        onkeydown: (e) => { if (e.key === 'Enter') { e.preventDefault(); addCustom(); } },
      });
      input.value = state.customDraft[i] || '';
      box.append(el('section', { class: 'strip', 'aria-label': 'Strip ' + (i + 1) },
        el('div', { class: 'strip-head' },
          el('span', { class: 'swatch', style: 'background:' + STRIP_COLORS[i % STRIP_COLORS.length] }),
          el('h2', null, 'Strip ' + (i + 1)),
          i > 0 ? el('button', { type: 'button', class: 'icon-btn', id: 'remove-' + i, 'aria-label': 'Remove strip ' + (i + 1), onclick: () => changeConfig((c) => { c.strips.splice(i, 1); c.joints.splice(i - 1, 1); }) }, 'Remove') : null),
        el('div', { class: 'field' },
          el('span', { class: 'label' }, 'Half-twists before taping the ends'),
          el('div', { class: 'row' },
            el('div', { class: 'stepper' },
              el('button', { type: 'button', id: 'tw-' + i + '-minus', 'aria-label': 'One fewer half-twist', onclick: () => changeConfig((c) => (c.strips[i].halfTwists = Math.max(-C.MAX_TWISTS, s.halfTwists - 1))) }, '−'),
              el('output', { 'aria-live': 'polite' }, (s.halfTwists > 0 ? '+' : '') + s.halfTwists),
              el('button', { type: 'button', id: 'tw-' + i + '-plus', 'aria-label': 'One more half-twist', onclick: () => changeConfig((c) => (c.strips[i].halfTwists = Math.min(C.MAX_TWISTS, s.halfTwists + 1))) }, '+')),
            el('span', { class: 'twist-name' }, twistName(s.halfTwists)))),
        el('div', { class: 'field' },
          el('span', { class: 'label' }, 'Cut along the line this far across'),
          el('div', { class: 'chips' }, chips, extra),
          el('div', { class: 'custom' }, input, el('button', { type: 'button', id: 'custom-add-' + i, onclick: addCustom }, 'Add')),
          state.errors[i] ? el('p', { class: 'note error' }, state.errors[i]) : null,
          s.cuts.length === 0 ? el('p', { class: 'note' }, 'No cut on this strip.') : null,
          notes.map((t) => el('p', { class: 'note' }, t)))));
    });
    if (active) { const a = document.getElementById(active); if (a) a.focus(); }

    $('add-strip').hidden = cfg.strips.length >= C.MAX_STRIPS;
    const hasCuts = state.model.cutPaths.length > 0;
    $('cut-btn').disabled = !hasCuts || state.phase !== 'setup';
    $('reset-btn').disabled = state.phase === 'setup';
    $('gap').disabled = state.phase !== 'cut' || state.view === 'pull';
    const pullBtn = $('pull-btn');
    pullBtn.disabled = state.phase !== 'cut';
    pullBtn.setAttribute('aria-pressed', String(state.view === 'pull'));
    pullBtn.textContent = state.view === 'pull' ? 'Back to the cut' : 'Pull apart';
    $('status').textContent = state.phase === 'setup'
      ? (hasCuts ? 'Ready to cut · red lines show where' : 'Pick where to cut')
      : state.phase === 'cutting' ? 'Cutting…'
      : state.view === 'pull' ? (state.sim.done ? 'Pulled apart' : state.sim.shaking ? 'Pulling and wiggling…' : 'Pulling apart…')
      : 'Cut · ' + state.result.pieces.length + (state.result.pieces.length === 1 ? ' piece' : ' pieces');
  }

  // ----------------------------------------------------------- results UI --

  function describeBefore() {
    const r = state.before;
    if (r.pieces.length !== 1) return '';
    const p = r.pieces[0];
    const n = state.config.strips.length;
    const what = n === 1 ? 'The strip' : 'The ' + n + ' taped strips';
    if (p.type === 'mobius' || p.type === 'band') return what + ' before cutting: ' + p.title.toLowerCase() + ', ' + p.facts.slice(0, 2).join(', ') + '.';
    return what + ' before cutting: a single ' + (p.orientable ? 'two-sided' : 'one-sided') + ' shape with ' + p.edgeCount + (p.edgeCount === 1 ? ' edge' : ' edges') + '.';
  }

  function renderResults() {
    const box = $('results');
    box.textContent = '';
    const before = describeBefore().replace('möbius', 'Möbius');
    if (state.phase !== 'cut') {
      box.append(
        el('p', { class: 'headline' }, state.model.cutPaths.length
          ? 'Make a guess, then press Cut. One piece or several? Linked or loose?'
          : 'Choose where to cut on at least one strip.'),
        el('p', { class: 'before' }, before));
      return;
    }
    const r = state.result;
    box.append(el('p', { class: 'headline' }, r.summary));
    if (state.view === 'pull') box.append(pullVerdict());
    else if (r.pieces.length > 1) box.append(el('p', { class: 'before' }, 'Not sure if they’re hooked together? Press Pull apart to tug the pieces away from each other and watch.'));
    const list = el('div', { class: 'pieces' });
    r.pieces.forEach((p, i) => {
      const facts = p.facts.map((f, k) => el('li', { class: k === 0 ? 'side' : '' }, f));
      for (const l of p.linkedWith) {
        facts.push(el('li', { class: 'linked' }, (l.tangled ? 'tangled with #' : 'interlocked with #') + (l.piece + 1) + (l.lk > 1 ? ' (wraps ' + l.lk + '×)' : '')));
      }
      const hidden = state.hidden.has(i);
      const card = el('div', {
        class: 'piece' + (hidden ? ' hidden-piece' : ''), role: 'button', tabindex: '0', id: 'piece-' + i,
        'aria-pressed': String(state.focus === i),
        'aria-label': 'Piece ' + (i + 1) + ', ' + p.title + '. Select to highlight it.',
        onclick: () => { state.focus = state.focus === i ? -1 : i; state.hidden.delete(i); redraw(); renderResults(); },
        onkeydown: (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.currentTarget.click(); } },
      },
      el('span', { class: 'swatch', style: 'background:' + PIECE_COLORS[i % PIECE_COLORS.length] }),
      el('h3', null, p.title, el('small', null, '#' + (i + 1))),
      el('button', {
        type: 'button', class: 'eye', id: 'eye-' + i,
        onclick: (e) => { e.stopPropagation(); if (hidden) state.hidden.delete(i); else { state.hidden.add(i); if (state.focus === i) state.focus = -1; } redraw(); renderResults(); },
      }, hidden ? 'Show' : 'Hide'),
      el('ul', { class: 'facts' }, facts));
      list.append(card);
    });
    box.append(list);
    if (before) box.append(el('p', { class: 'before' }, before));
  }

  function pullVerdict() {
    const sim = state.sim, r = state.result;
    const name = (i) => '#' + (i + 1);
    const lines = [];
    if (r.pieces.length === 1) {
      lines.push(sim.done
        ? 'There’s only one piece, so nothing comes apart. Pulled loose, it shows its real shape' + (r.pieces[0].knot && r.pieces[0].knot.knotted ? ', knot and all.' : '.')
        : 'Loosening the piece to show its real shape…');
    } else if (!sim.done) {
      lines.push(sim.shaking
        ? 'Some pieces are snagged. Wiggling them to see if they slide free…'
        : 'Pulling the pieces away from each other. They can’t pass through each other, just like paper.');
    } else {
      const hooked = sim.pairs.filter((p) => p.linked && p.touching);
      const free = sim.pairs.filter((p) => !p.linked && !p.touching);
      const caught = sim.pairs.filter((p) => !p.linked && p.touching);
      for (const p of hooked) lines.push(name(p.a) + ' and ' + name(p.b) + ' stay hooked together like chain links. They can’t be separated without cutting.');
      if (free.length && !hooked.length && !caught.length) lines.push('All the pieces slid free of each other. They are separate shapes.');
      else for (const p of free) lines.push(name(p.a) + ' and ' + name(p.b) + ' slid free of each other.');
      for (const p of caught) lines.push(name(p.a) + ' and ' + name(p.b) + ' are still snagged, but they aren’t linked. With more wiggling they would come apart.');
    }
    return el('p', { class: 'verdict' }, el('strong', null, sim.done ? 'Pulled apart' : 'Pulling…'), lines.map((t) => el('span', null, t)));
  }

  // --------------------------------------------------------------- wiring --

  const presetSel = $('preset');
  presetSel.append(el('option', { value: '' }, 'Custom setup'));
  PRESETS.forEach((p, i) => presetSel.append(el('option', { value: String(i) }, p.name)));
  presetSel.value = String(DEFAULT_PRESET);
  presetSel.addEventListener('change', () => {
    if (presetSel.value === '') return;
    state.config = presetConfig(PRESETS[Number(presetSel.value)]);
    state.errors = {};
    state.customDraft = {};
    rebuild(false);
  });
  // Any hand edit turns the preset menu back to "Custom setup".
  $('strips').addEventListener('click', () => (presetSel.value = ''), true);
  $('add-strip').addEventListener('click', () => {
    presetSel.value = '';
    changeConfig((c) => { c.strips.push({ halfTwists: 1, cuts: [1 / 2] }); c.joints.push('orthogonal'); });
    frameView();
  });
  $('cut-btn').addEventListener('click', () => doCut(true));
  $('reset-btn').addEventListener('click', () => rebuild(true));
  $('gap').addEventListener('input', (e) => {
    state.gap = Number(e.target.value);
    if (state.phase === 'cut') drawPieces(state.gap);
  });
  $('edges-btn').addEventListener('click', (e) => {
    state.edges = !state.edges;
    e.currentTarget.setAttribute('aria-pressed', String(state.edges));
    if (state.phase !== 'cutting') redraw();
  });
  $('view-btn').addEventListener('click', frameView);
  $('pull-btn').addEventListener('click', () => (state.view === 'pull' ? stopPull() : startPull()));

  const onTheme = () => { buildMat(); if (state.phase !== 'cutting') redraw(); };
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', onTheme);
  new MutationObserver(onTheme).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  rebuild(false);
  buildMat();
  resize();
  doCut(false); // open on a finished experiment so the first view shows a result
  requestAnimationFrame(loop);
})();
