// Exterior and symbolic locations: night city, street, Golgotha, cosmos, glory,
// sunrise road, scroll, Kidron valley, end card.
(function () {
  const { f, spline, tufts, poly, mix, shade, clamp, lerp, rng, lg, rg } = U;
  const OUT = '#2a1910';

  S.sky = (id, stops, x = -500, y = -500, w = 2080, h = 2920) =>
    `<defs>${lg(id, stops)}</defs><rect x="${x}" y="${y}" width="${w}" height="${h}" fill="url(#${id})"/>`;

  S.moon = function (x, y, r, glow = 1) {
    return `<circle cx="${x}" cy="${y}" r="${r * 5}" fill="url(#moonGlow)" opacity="${glow}"/>` +
      `<circle cx="${x}" cy="${y}" r="${r}" fill="#f4f1e4"/>` +
      `<circle cx="${x - r * 0.3}" cy="${y - r * 0.2}" r="${r * 0.22}" fill="#dcd8c6" opacity="0.7"/>` +
      `<circle cx="${x + r * 0.25}" cy="${y + r * 0.3}" r="${r * 0.15}" fill="#dcd8c6" opacity="0.6"/>` +
      `<circle cx="${x + r * 0.35}" cy="${y - r * 0.35}" r="${r * 0.1}" fill="#dcd8c6" opacity="0.5"/>`;
  };

  // Radial light rays (wedges) around (cx, cy).
  S.rays = function (id, cx, cy, n, len, color, op, rot = 0, spread = 0.5) {
    let d = '';
    for (let i = 0; i < n; i++) {
      const a = ((i / n) * 360 + rot) * Math.PI / 180, w = ((360 / n) * spread * Math.PI) / 180 / 2;
      d += `M${cx},${cy} L${f(cx + Math.cos(a - w) * len)},${f(cy + Math.sin(a - w) * len)} L${f(cx + Math.cos(a + w) * len)},${f(cy + Math.sin(a + w) * len)}Z`;
    }
    return `<defs>${rg(id, [[0, color, op], [0.7, color, op * 0.35], [1, color, 0]], cx, cy, len, 'gradientUnits="userSpaceOnUse" fx="' + cx + '" fy="' + cy + '"')}</defs><path d="${d}" fill="url(#${id})"/>`;
  };

  S.hill = (pts, fill, extra = '') => `<path d="${spline(pts, false)} L${pts[pts.length - 1][0]},2600 L${pts[0][0]},2600Z" fill="${fill}" ${extra}/>`;

  // Olive tree: gnarled trunk + clumps of foliage.
  S.olive = function (x, y, sc, seed, trunk = '#1d2430', leaf = '#26364a', hi = '#3a5170') {
    const r = rng(seed);
    let s = `<g transform="translate(${f(x)},${f(y)}) scale(${f(sc)})">`;
    s += `<path d="M-18,0 C-14,-40 -30,-80 -10,-120 C-4,-140 -20,-170 -6,-190 L8,-188 C0,-160 18,-140 12,-110 C26,-80 14,-40 22,0Z" fill="${trunk}"/>`;
    s += `<path d="M-8,-120 C-40,-140 -70,-150 -90,-170 M6,-130 C40,-150 60,-170 84,-176" stroke="${trunk}" stroke-width="10" fill="none" stroke-linecap="round"/>`;
    for (let i = 0; i < 9; i++) {
      const cx = (r() - 0.5) * 220, cy = -170 - r() * 110, rx = 50 + r() * 50, ry = 32 + r() * 26;
      s += `<ellipse cx="${f(cx)}" cy="${f(cy)}" rx="${f(rx)}" ry="${f(ry)}" fill="${leaf}"/>`;
      s += `<ellipse cx="${f(cx - rx * 0.2)}" cy="${f(cy - ry * 0.35)}" rx="${f(rx * 0.6)}" ry="${f(ry * 0.4)}" fill="${hi}" opacity="0.5"/>`;
    }
    return s + '</g>';
  };

  S.pine = function (x, y, sc, col) {
    return `<g transform="translate(${f(x)},${f(y)}) scale(${f(sc)})" fill="${col}">` +
      `<path d="M-8,0 C-6,-120 -2,-240 -30,-330 L-18,-334 C6,-250 10,-140 10,0Z"/>` +
      `<path d="M-26,-330 C-80,-360 -150,-362 -190,-376 C-150,-410 -40,-430 40,-420 C120,-412 190,-396 210,-372 C160,-352 60,-336 -26,-330Z"/>` +
      '</g>';
  };
  S.cypress = (x, y, sc, col) =>
    `<path transform="translate(${f(x)},${f(y)}) scale(${f(sc)})" d="M0,-420 C22,-330 40,-150 30,0 L-30,0 C-40,-150 -22,-330 0,-420Z" fill="${col}"/>`;

  // Flat-roofed house block.
  S.house = function (x, y, w, h, col, seed, lit = 0.3, roofCol) {
    const r = rng(seed);
    let s = `<rect x="${f(x)}" y="${f(y - h)}" width="${f(w)}" height="${f(h)}" fill="${col}"/>`;
    s += `<rect x="${f(x - 4)}" y="${f(y - h - 10)}" width="${f(w + 8)}" height="12" fill="${roofCol || shade(col, 0.12)}"/>`;
    s += `<rect x="${f(x + w * 0.62)}" y="${f(y - h)}" width="${f(w * 0.38)}" height="${f(h)}" fill="#000" opacity="0.18"/>`;
    const nw = Math.max(1, Math.floor(w / 70)), nh = Math.max(1, Math.floor(h / 90));
    for (let i = 0; i < nw; i++) for (let j = 0; j < nh; j++) {
      if (r() < 0.45) continue;
      const wx = x + 18 + i * (w - 30) / nw, wy = y - h + 26 + j * (h - 30) / nh;
      const on = r() < lit;
      s += `<path d="${S.archPath(wx + 10, wy, 20, 30)}" fill="${on ? '#ffc76a' : '#0c1222'}" opacity="${on ? 0.95 : 0.8}"/>`;
    }
    return s;
  };

  S.cross = (x, y, h, col) =>
    `<rect x="${f(x - h * 0.035)}" y="${f(y - h)}" width="${f(h * 0.07)}" height="${f(h)}" fill="${col}"/>` +
    `<rect x="${f(x - h * 0.28)}" y="${f(y - h * 0.8)}" width="${f(h * 0.56)}" height="${f(h * 0.065)}" fill="${col}"/>`;

  // Stone block wall.
  S.stoneWall = function (x0, y0, w, h, seed, base = '#3c4656', lineCol = '#1a1f29') {
    const r = rng(seed);
    let s = `<rect x="${x0}" y="${y0}" width="${w}" height="${h}" fill="${base}"/>`;
    let d = '', blocks = '';
    for (let y = y0, row = 0; y < y0 + h; y += 96, row++) {
      let x = x0 - (row % 2) * 70;
      while (x < x0 + w) {
        const bw = 120 + r() * 90;
        blocks += `<rect x="${f(x + 3)}" y="${f(y + 3)}" width="${f(bw - 6)}" height="90" rx="6" fill="${shade(base, (r() - 0.5) * 0.18)}"/>`;
        d += `M${f(x)},${f(y)} L${f(x)},${f(y + 96)}`;
        x += bw;
      }
      d += `M${x0},${f(y)} L${x0 + w},${f(y)}`;
    }
    return s + blocks + `<path d="${d}" stroke="${lineCol}" stroke-width="4" opacity="0.7"/>`;
  };

  // Perspective cobblestones on the ground plane between horizonY and the bottom.
  S.cobbles = function (horizonY, vpX, seed, base = '#2c3442', hi = '#4d5a6e') {
    const r = rng(seed);
    let s = `<rect x="-500" y="${horizonY}" width="2080" height="${2400 - horizonY}" fill="${base}"/>`;
    for (let row = 0; row < 26; row++) {
      const t0 = row / 26, t1 = (row + 1) / 26;
      const y = horizonY + Math.pow(t0, 1.6) * (2000 - horizonY), y1 = horizonY + Math.pow(t1, 1.6) * (2000 - horizonY);
      const hgt = y1 - y, scale = (y - horizonY) / (2000 - horizonY) + 0.05;
      const sw = 60 + 220 * scale;
      for (let x = -600 + (row % 2) * sw * 0.5; x < 1700; x += sw) {
        const cx = vpX + (x - vpX), w = sw * 0.86;
        s += `<ellipse cx="${f(cx + w / 2)}" cy="${f(y + hgt / 2)}" rx="${f(w / 2)}" ry="${f(hgt * 0.42)}" fill="${shade(hi, (r() - 0.6) * 0.3)}" opacity="0.85"/>`;
      }
    }
    return s;
  };

  S.door = function (x, y, w, h, openAmt = 0) {
    let s = `<path d="${S.archPath(x, y - h, w + 30, h + 6)}" fill="#1a1410"/>`;
    s += `<path d="${S.archPath(x, y - h + 8, w, h - 8)}" fill="#ffb455" opacity="${f(0.85 * openAmt)}"/>`;
    const dw = w * (1 - 0.55 * openAmt);
    s += `<g><path d="${S.archPath(x - (w - dw) / 2, y - h + 8, dw, h - 8)}" fill="#6a4426" stroke="#1a1008" stroke-width="3"/>`;
    for (let i = 1; i < 5; i++) s += `<path d="M${f(x - w / 2 + (w - dw) * 0 + i * dw / 5 - (w - dw) / 2 + (w - dw) / 2)},${f(y - h + 40)} L${f(x - w / 2 + i * dw / 5)},${f(y)}" stroke="#3a2412" stroke-width="3" opacity="0.8"/>`;
    s += `<rect x="${f(x - w / 2)}" y="${f(y - h * 0.62)}" width="${f(dw)}" height="14" fill="#2a2a2e"/><rect x="${f(x - w / 2)}" y="${f(y - h * 0.25)}" width="${f(dw)}" height="14" fill="#2a2a2e"/></g>`;
    return s;
  };

  S.torch = (x, y) =>
    `<path d="M${x - 8},${y} L${x + 8},${y} L${x + 4},${y + 70} L${x - 4},${y + 70}Z" fill="#3a2414" stroke="#120a06" stroke-width="2"/>` +
    `<rect x="${x - 26}" y="${y + 50}" width="52" height="10" rx="4" fill="#2a2a2e"/>`;

  // Open scroll seen from slightly above, with rows of "writing".
  S.scroll = function (cx, cy, w, h, seed) {
    const r = rng(seed);
    let s = '<defs>' + lg('sc-paper', [[0, '#f3e2bb'], [0.5, '#e8d2a2'], [1, '#c9ab76']], 0, 0, 0, 1) + lg('sc-roll', [[0, '#e6cf9f'], [0.5, '#fff1cc'], [1, '#b8955e']], 0, 0, 1, 0) + '</defs>';
    s += `<ellipse cx="${cx}" cy="${cy + h / 2 + 20}" rx="${w * 0.62}" ry="40" fill="#000" opacity="0.35"/>`;
    s += `<path d="M${cx - w / 2},${cy - h / 2} C${cx - w / 4},${cy - h / 2 - 16} ${cx + w / 4},${cy - h / 2 + 10} ${cx + w / 2},${cy - h / 2} L${cx + w / 2},${cy + h / 2} C${cx + w / 4},${cy + h / 2 + 10} ${cx - w / 4},${cy + h / 2 - 16} ${cx - w / 2},${cy + h / 2}Z" fill="url(#sc-paper)" stroke="${OUT}" stroke-width="2.4"/>`;
    // columns of text strokes (abstract, not a real script)
    for (let col = 0; col < 3; col++) {
      const x0 = cx - w / 2 + 60 + col * (w - 120) / 3, cw = (w - 120) / 3 - 40;
      for (let row = 0; row < 11; row++) {
        const y = cy - h / 2 + 50 + row * (h - 100) / 11;
        let x = x0;
        let d = '';
        while (x < x0 + cw) { const sw = 8 + r() * 26; if (x + sw > x0 + cw) break; const k = (r() - 0.5) * 7; d += `M${f(x)},${f(y + k * 0.3)} q${f(sw * 0.3)},${f(-3 - r() * 3)} ${f(sw * 0.55)},0 t${f(sw * 0.45)},${f(1 + r() * 2)}`; x += sw + 7 + r() * 7; }
        s += `<path d="${d}" fill="none" stroke="#3a2412" stroke-width="4.5" stroke-linecap="round" opacity="0.6"/>`;
      }
    }
    for (const sgn of [-1, 1]) {
      const x = cx + sgn * (w / 2 + 22);
      s += `<rect x="${x - 30}" y="${cy - h / 2 - 30}" width="60" height="${h + 60}" rx="28" fill="url(#sc-roll)" stroke="${OUT}" stroke-width="2.4"/>`;
      s += `<rect x="${x - 9}" y="${cy - h / 2 - 70}" width="18" height="${h + 140}" rx="8" fill="#6a4020" stroke="${OUT}" stroke-width="2"/>`;
      s += `<ellipse cx="${x}" cy="${cy - h / 2 - 72}" rx="20" ry="10" fill="#8a5428" stroke="${OUT}" stroke-width="2"/>`;
      s += `<ellipse cx="${x}" cy="${cy + h / 2 + 72}" rx="20" ry="10" fill="#8a5428" stroke="${OUT}" stroke-width="2"/>`;
    }
    return s;
  };

  // Soft nebula clouds for the cosmos shot.
  S.nebula = function (seed, cols) {
    const r = rng(seed);
    let s = '<defs>';
    cols.forEach((c, i) => { s += rg('nb' + seed + i, [[0, c, 0.55], [0.6, c, 0.18], [1, c, 0]]); });
    s += '</defs>';
    for (let i = 0; i < 16; i++) {
      const c = Math.floor(r() * cols.length);
      s += `<ellipse cx="${f(-200 + r() * 1480)}" cy="${f(-100 + r() * 2120)}" rx="${f(200 + r() * 420)}" ry="${f(140 + r() * 320)}" fill="url(#nb${seed}${c})" transform="rotate(${f(r() * 180)})"/>`;
    }
    return s;
  };

  // ------------------------------------------------------------------ people generator
  // Random believers of many nations and ages, for the candle and crowd shots.
  const SKIN = [['#f0cfb0', '#c99c7a'], ['#e3b48e', '#b8865f'], ['#d3a07a', '#a8724f'], ['#c48f69', '#956042'], ['#a8704c', '#7a4c30'], ['#8a5638', '#5e3620'], ['#6b4128', '#462714'], ['#5a3420', '#3a1f10']];
  const HAIR = [['#1e140e', '#0e0906', '#4a382c'], ['#3a2416', '#22140b', '#6b4a33'], ['#6b3a22', '#45230f', '#9a5d38'], ['#8a6a48', '#5e4630', '#b8946a'], ['#cfcfcf', '#9a9a9a', '#ffffff'], ['#2a1a12', '#140c08', '#5a4030']];
  const CLOTH = ['#3f5878', '#7b4e2c', '#6f7f4a', '#8b5a3a', '#7a2e2e', '#4a5a6a', '#6a4a7a', '#b8956a', '#2f5d62', '#9a6a2a', '#56406a', '#3c6a4a', '#a0522d', '#5a6e8c'];
  const VEIL = [['#d8c6a2', '#b39e78'], ['#6d86a8', '#4d6688'], ['#a8505a', '#7a3440'], ['#e8e0d0', '#c4b9a4'], ['#7a8a5a', '#5a6a3c'], ['#c79a5a', '#9a7038']];

  RIG.person = function (seed, opt = {}) {
    const r = rng(seed * 31 + 7);
    const pick = (a) => a[Math.floor(r() * a.length)];
    const [skin, skinShade] = pick(SKIN);
    const [hair, hairShade, hairHi] = opt.old ? HAIR[4] : pick(HAIR.slice(0, 4).concat([HAIR[5]]));
    const robe = pick(CLOTH), mantle = r() < 0.6 ? pick(CLOTH) : null;
    const kind = opt.kind || (r() < 0.12 ? 'child' : r() < 0.5 ? 'female' : 'male');
    const p = {
      skin, skinShade, lip: mix(skinShade, '#b05050', 0.35), hair, hairShade, hairHi, beard: hair, beardHi: hairHi, brow: hairShade,
      robe, robeShade: shade(robe, -0.25), robeLine: shade(robe, -0.45), mantle, mantleShade: mantle ? shade(mantle, -0.25) : null, trim: null,
      eye: pick(['#4a2e1a', '#3a2414', '#5a3a22', '#2e1a0e', '#5a6a7a']), age: opt.old ? 0.7 : r() * 0.3,
    };
    if (kind === 'female') {
      p.female = true; p.lip = mix(skinShade, '#c0505a', 0.5);
      if (r() < 0.6) { const [v, vs] = pick(VEIL); p.veil = v; p.veilShade = vs; p.hairStyle = 'veil'; } else p.hairStyle = 'longFemale';
      p.beardStyle = 'none';
    } else if (kind === 'child') {
      p.child = true; p.hairStyle = r() < 0.5 ? 'short' : 'wavy'; p.beardStyle = 'none';
    } else {
      p.hairStyle = pick(['short', 'curly', 'headcloth', 'wavy', 'short']);
      if (p.hairStyle === 'headcloth') { const [c, cs] = pick(VEIL); p.cloth = c; p.clothShade = cs; p.band = pick(['#5a3a2a', '#2a2a3a', '#7a2f2f']); }
      p.beardStyle = pick(['full', 'short', 'none', 'stubble', 'short']);
      p.gray = opt.old ? 0.7 : 0;
    }
    return { pal: p, kind };
  };
})();
