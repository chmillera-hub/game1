// Backgrounds, props and lighting layers for every location in the film.
(function () {
  const { f, spline, tufts, poly, mix, shade, clamp, lerp, rng, lg, rg } = U;
  const OUT = '#2a1910';
  const S = {};
  window.S = S;

  const archPath = (x, y, w, h) =>
    `M${f(x - w / 2)},${f(y + h)} L${f(x - w / 2)},${f(y + w / 2)} A${f(w / 2)},${f(w / 2)} 0 0 1 ${f(x + w / 2)},${f(y + w / 2)} L${f(x + w / 2)},${f(y + h)}Z`;
  S.archPath = archPath;

  function stars(n, x0, y0, w, h, seed, maxR = 2.4, op = 0.9) {
    const r = rng(seed);
    let s = '';
    for (let i = 0; i < n; i++) {
      const x = x0 + r() * w, y = y0 + r() * h, rad = 0.6 + r() * maxR, a = 0.35 + r() * 0.65;
      s += `<circle cx="${f(x)}" cy="${f(y)}" r="${f(rad)}" fill="#fffbe8" opacity="${f(a * op)}"/>`;
    }
    return s;
  }
  S.stars = stars;

  // Large soft blotches that give painted plaster/stone some life.
  function blotches(n, x0, y0, w, h, seed, dark = '#000', light = '#ffe2b8', op = 0.06) {
    const r = rng(seed);
    let s = '';
    for (let i = 0; i < n; i++) {
      const x = x0 + r() * w, y = y0 + r() * h, rx = 80 + r() * 260, ry = 60 + r() * 200;
      s += `<ellipse cx="${f(x)}" cy="${f(y)}" rx="${f(rx)}" ry="${f(ry)}" fill="${r() < 0.55 ? dark : light}" opacity="${f(op * (0.4 + r()))}"/>`;
    }
    return s;
  }

  // ------------------------------------------------------------------ upper room
  S.roomWall = function (o = {}) {
    const win = o.win || { x: 800, y: 300, w: 300, h: 540 };
    const lamps = o.lamps || [[150, 780]];
    let s = '<defs>' +
      lg('rw-wall', [[0, '#22150c'], [0.22, '#4e321f'], [0.55, '#6c4529'], [0.85, '#563620'], [1, '#2e1d11']]) +
      lg('rw-sky', [[0, '#081129'], [0.6, '#132449'], [1, '#22355f']]) +
      lg('rw-reveal', [[0, '#8a5e3c'], [0.5, '#6a4529'], [1, '#33200f']], 0, 0, 1, 0) +
      rg('rw-glow', [[0, '#ffb565', 0.55], [0.45, '#ff9a48', 0.18], [1, '#ff8a3a', 0]]) +
      rg('rw-horizon', [[0, '#3c4f86', 0.7], [1, '#3c4f86', 0]]) +
      '</defs>';
    s += `<rect x="-700" y="-300" width="2480" height="2600" fill="url(#rw-wall)"/>`;
    s += blotches(16, -600, -200, 2300, 2400, o.seed || 5, '#1a0f08', '#f2c08a', 0.07);
    for (const [lx, ly] of lamps) s += `<circle cx="${lx}" cy="${ly}" r="${o.glowR || 760}" fill="url(#rw-glow)"/>`;
    // lower wall band and ledge
    s += `<rect x="-700" y="${o.ledge || 1240}" width="2480" height="1200" fill="#2b1a0f" opacity="0.38"/>`;
    s += `<rect x="-700" y="${(o.ledge || 1240) - 14}" width="2480" height="16" fill="#8a5c38" opacity="0.5"/>`;
    // ceiling beam
    if (o.beam !== false) {
      s += `<rect x="-700" y="-300" width="2480" height="${(o.beamY || 120) + 300}" fill="#1e120a"/>`;
      s += `<rect x="-700" y="${(o.beamY || 120) - 22}" width="2480" height="22" fill="#4a2e1a"/>`;
      for (let x = -640; x < 1800; x += 300) s += `<rect x="${x}" y="-300" width="60" height="${(o.beamY || 120) + 300}" fill="#2c1b0f" opacity="0.8"/>`;
    }
    // arched window: reveal, sky, stars, hills, distant lights
    const W2 = win.w + 54;
    s += `<path d="${archPath(win.x, win.y - 27, W2, win.h + 40)}" fill="url(#rw-reveal)"/>`;
    s += `<clipPath id="rw-winclip"><path d="${archPath(win.x, win.y, win.w, win.h)}"/></clipPath>`;
    s += `<g clip-path="url(#rw-winclip)">`;
    s += `<rect x="${win.x - win.w}" y="${win.y - 10}" width="${win.w * 2}" height="${win.h + 20}" fill="url(#rw-sky)"/>`;
    s += stars(46, win.x - win.w / 2, win.y, win.w, win.h * 0.7, 21, 2.2);
    s += `<ellipse cx="${win.x}" cy="${win.y + win.h * 0.82}" rx="${win.w}" ry="${win.h * 0.3}" fill="url(#rw-horizon)"/>`;
    const hy = win.y + win.h * 0.78;
    s += `<path d="M${win.x - win.w},${hy + 30} C${win.x - win.w * 0.6},${hy - 40} ${win.x - win.w * 0.2},${hy + 10} ${win.x},${hy - 16} C${win.x + win.w * 0.3},${hy - 46} ${win.x + win.w * 0.6},${hy + 6} ${win.x + win.w},${hy - 10} L${win.x + win.w},${win.y + win.h + 20} L${win.x - win.w},${win.y + win.h + 20}Z" fill="#0b1328"/>`;
    const r = rng(77);
    for (let i = 0; i < 9; i++) s += `<rect x="${f(win.x - win.w * 0.45 + r() * win.w * 0.9)}" y="${f(hy + 20 + r() * 40)}" width="4" height="3" fill="#ffcf7a" opacity="${f(0.5 + r() * 0.5)}"/>`;
    s += '</g>';
    s += `<path d="${archPath(win.x, win.y, win.w, win.h)}" fill="none" stroke="#1a0f08" stroke-width="4" opacity="0.6"/>`;
    s += `<rect x="${win.x - W2 / 2 - 6}" y="${win.y + win.h + 8}" width="${W2 + 12}" height="26" rx="4" fill="#8a5c38"/>`;
    s += `<rect x="${win.x - W2 / 2 - 6}" y="${win.y + win.h + 30}" width="${W2 + 12}" height="10" fill="#3a2414"/>`;
    // wall lamp niches
    for (const [lx, ly] of lamps) {
      s += `<path d="${archPath(lx, ly - 120, 150, 170)}" fill="#3a2414"/>`;
      s += `<path d="${archPath(lx, ly - 112, 134, 158)}" fill="#7a4e2c" opacity="0.65"/>`;
      s += S.oilLamp(lx, ly + 30, 1);
    }
    return s;
  };

  S.oilLamp = function (x, y, sc) {
    return `<g transform="translate(${f(x)},${f(y)}) scale(${f(sc)})">` +
      `<path d="M-38,0 C-38,-18 22,-22 40,-8 L58,-14 C64,-13 64,-6 58,-3 L40,4 C24,14 -38,16 -38,0Z" fill="#9a6640" stroke="${OUT}" stroke-width="2.2"/>` +
      `<ellipse cx="-6" cy="-12" rx="14" ry="5" fill="#4a2c18"/>` +
      `<path d="M-30,-4 C-10,-12 20,-12 36,-4" fill="none" stroke="#c48a5c" stroke-width="3" opacity="0.6"/>` +
      '</g>';
  };

  // Flickering flames + glows drawn in a screen-blended layer.
  S.flames = function (gt, list) {
    let s = '<defs>' + rg('fl-glow', [[0, '#ffd890', 0.9], [0.3, '#ffae50', 0.35], [1, '#ff8a30', 0]]) + '</defs>';
    list.forEach(([x, y, sc, seed], i) => {
      sc = sc || 1;
      const fl = 1 + 0.12 * U.noise(gt * 6 + i * 3, seed || i) + 0.05 * U.noise(gt * 17, (seed || i) + 9);
      const sway = 3 * U.noise(gt * 2.5, (seed || i) + 2);
      s += `<g transform="translate(${f(x)},${f(y)}) scale(${f(sc)})">` +
        `<circle cx="0" cy="-18" r="${f(150 * fl)}" fill="url(#fl-glow)" opacity="0.65"/>` +
        `<path d="M0,0 C-11,-10 -10,-28 ${f(sway)},${f(-48 * fl)} C10,-28 11,-10 0,0Z" fill="#ffc04d"/>` +
        `<path d="M0,-2 C-5,-8 -5,-20 ${f(sway * 0.6)},${f(-34 * fl)} C5,-20 5,-8 0,-2Z" fill="#fff6d0"/>` +
        '</g>';
    });
    return s;
  };

  S.goblet = function (x, y, sc) {
    return `<g transform="translate(${f(x)},${f(y)}) scale(${f(sc)})">` +
      `<ellipse cx="0" cy="0" rx="34" ry="8" fill="#000" opacity="0.3"/>` +
      `<path d="M-26,0 C-24,-8 -8,-10 -6,-20 L-5,-48 C-22,-54 -34,-72 -34,-104 L34,-104 C34,-72 22,-54 5,-48 L6,-20 C8,-10 24,-8 26,0Z" fill="#a8783e" stroke="${OUT}" stroke-width="2.2"/>` +
      `<ellipse cx="0" cy="-104" rx="34" ry="8" fill="#4a1218" stroke="${OUT}" stroke-width="2"/>` +
      `<path d="M-24,-96 C-22,-76 -14,-62 -4,-56" fill="none" stroke="#f0cf8a" stroke-width="4" opacity="0.55" stroke-linecap="round"/>` +
      '</g>';
  };

  S.cup = function (x, y, sc, col = '#9a5a36') {
    return `<g transform="translate(${f(x)},${f(y)}) scale(${f(sc)})">` +
      `<ellipse cx="0" cy="2" rx="40" ry="9" fill="#000" opacity="0.3"/>` +
      `<path d="M-30,0 C-36,-30 -38,-56 -36,-70 L36,-70 C38,-56 36,-30 30,0 C14,6 -14,6 -30,0Z" fill="${col}" stroke="${OUT}" stroke-width="2.2"/>` +
      `<ellipse cx="0" cy="-70" rx="36" ry="9" fill="${shade(col, -0.45)}" stroke="${OUT}" stroke-width="2"/>` +
      `<path d="M-24,-60 C-26,-40 -24,-20 -20,-6" fill="none" stroke="#ffd9a8" stroke-width="4" opacity="0.35" stroke-linecap="round"/>` +
      '</g>';
  };

  S.jug = function (x, y, sc) {
    return `<g transform="translate(${f(x)},${f(y)}) scale(${f(sc)})">` +
      `<ellipse cx="0" cy="2" rx="58" ry="12" fill="#000" opacity="0.3"/>` +
      `<path d="M38,-120 C70,-118 74,-70 46,-56" fill="none" stroke="${OUT}" stroke-width="13"/>` +
      `<path d="M38,-120 C70,-118 74,-70 46,-56" fill="none" stroke="#a5603a" stroke-width="8"/>` +
      `<path d="M-22,-150 L22,-150 L20,-128 C50,-112 62,-70 52,-34 C46,-10 30,0 0,0 C-30,0 -46,-10 -52,-34 C-62,-70 -50,-112 -20,-128Z" fill="#b8693e" stroke="${OUT}" stroke-width="2.4"/>` +
      `<path d="M-40,-90 C-44,-60 -38,-30 -24,-14" fill="none" stroke="#ffcf9a" stroke-width="6" opacity="0.35" stroke-linecap="round"/>` +
      `<path d="M-50,-60 C-20,-52 20,-52 52,-60" fill="none" stroke="#7a3a1e" stroke-width="3" opacity="0.7"/>` +
      `<ellipse cx="0" cy="-150" rx="22" ry="6" fill="#4a2414" stroke="${OUT}" stroke-width="2"/>` +
      '</g>';
  };

  S.plate = function (x, y, sc) {
    return `<g transform="translate(${f(x)},${f(y)}) scale(${f(sc)})">` +
      `<ellipse cx="0" cy="4" rx="92" ry="22" fill="#000" opacity="0.25"/>` +
      `<ellipse cx="0" cy="0" rx="92" ry="22" fill="#c9a77a" stroke="${OUT}" stroke-width="2"/>` +
      `<ellipse cx="0" cy="-2" rx="66" ry="14" fill="#b08c60"/>` +
      '</g>';
  };

  S.breadPiece = function (x, y, sc, rot = 0) {
    return `<g transform="translate(${f(x)},${f(y)}) rotate(${rot}) scale(${f(sc)})">` +
      `<path d="M-40,0 C-40,-26 -10,-36 14,-30 C30,-26 40,-14 40,0 L28,-4 L20,6 L8,-2 L-2,8 L-12,-2 L-22,6 L-30,-2Z" fill="#c98a45" stroke="${OUT}" stroke-width="2"/>` +
      `<path d="M28,-4 L20,6 L8,-2 L-2,8 L-12,-2 L-22,6 L-30,-2 L-40,0 C-30,10 30,10 40,0Z" fill="#f1dcb4" stroke="${OUT}" stroke-width="1.6"/>` +
      `<path d="M-24,-18 C-10,-26 10,-28 24,-20" fill="none" stroke="#f0c27e" stroke-width="5" opacity="0.6" stroke-linecap="round"/>` +
      '</g>';
  };

  // A table seen from the front: top surface + front face, with props.
  S.table = function (o = {}) {
    const y = o.y || 1500, x0 = o.x0 === undefined ? -700 : o.x0, x1 = o.x1 === undefined ? 1780 : o.x1, depth = o.depth || 70;
    let s = '<defs>' + lg('tb-top', [[0, '#5a391f'], [1, '#8a5a33']]) + lg('tb-front', [[0, '#4a2d18'], [1, '#22140a']]) + '</defs>';
    s += `<rect x="${x0}" y="${y}" width="${x1 - x0}" height="${depth}" fill="url(#tb-top)" stroke="${OUT}" stroke-width="2.4"/>`;
    s += `<rect x="${x0}" y="${y + depth}" width="${x1 - x0}" height="900" fill="url(#tb-front)" stroke="${OUT}" stroke-width="2.4"/>`;
    s += `<rect x="${x0}" y="${y + depth - 6}" width="${x1 - x0}" height="6" fill="#b07a48" opacity="0.6"/>`;
    const r = rng(o.seed || 3);
    let g = '';
    for (let i = 0; i < 9; i++) { const yy = y + 8 + r() * (depth - 16); g += `M${x0},${f(yy)} C${f(x0 + 400)},${f(yy + r() * 6 - 3)} ${f(x1 - 400)},${f(yy + r() * 6 - 3)} ${x1},${f(yy)}`; }
    s += `<path d="${g}" fill="none" stroke="#3a2212" stroke-width="1.4" opacity="0.4"/>`;
    for (const p of o.props || []) s += p;
    return s;
  };

  // ------------------------------------------------------------------ grading overlays
  // A full-frame tint layer; use with blend 'soft-light' (light) or 'multiply' (shadow).
  S.tint = function (id, stops, cx, cy, r) {
    return `<defs>${rg(id, stops, cx, cy, r, 'gradientUnits="objectBoundingBox"')}</defs><rect x="0" y="0" width="1080" height="1920" fill="url(#${id})"/>`;
  };
  S.linearTint = function (id, stops, x1, y1, x2, y2) {
    return `<defs>${lg(id, stops, x1, y1, x2, y2)}</defs><rect x="0" y="0" width="1080" height="1920" fill="url(#${id})"/>`;
  };

  // Soft bokeh discs for out-of-focus lights.
  S.bokeh = function (list, seed, col = '#ffb866') {
    const r = rng(seed);
    let s = `<defs>${rg('bk-' + seed, [[0, col, 0.45], [0.75, col, 0.32], [1, col, 0]])}</defs>`;
    for (const [x, y, rad, a] of list) s += `<circle cx="${x}" cy="${y}" r="${rad}" fill="url(#bk-${seed})" opacity="${a === undefined ? 0.6 + r() * 0.4 : a}"/>`;
    return s;
  };
})();
