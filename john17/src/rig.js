// Character rigs drawn as SVG, styled after the reference video:
// soft cel-shaded skin, almond eyes with heavy upper lids, solid tufted beards,
// thin dark outlines and fold lines on robes.
(function () {
  const { f, spline, tufts, poly, mix, shade, clamp, lerp, rng } = U;
  const OUT = '#2a1910';

  // ---------------------------------------------------------------- palettes
  const cast = {
    jesus: {
      skin: '#d3a07a', skinShade: '#a8724f', lip: '#a4645a',
      hair: '#4a2c1c', hairShade: '#2c180e', hairHi: '#7a4f33',
      beard: '#3f2416', beardHi: '#6e4429', brow: '#2f1b10',
      robe: '#efe6d6', robeShade: '#c9b79d', robeLine: '#9c8a74',
      mantle: '#9b2424', mantleShade: '#6a1414', trim: '#d9a742',
      hairStyle: 'long', beardStyle: 'full', eye: '#5a3720', age: 0.15,
    },
    peter: {
      skin: '#c99872', skinShade: '#9b6a48', lip: '#9e5f52',
      hair: '#2e2420', hairShade: '#1a1310', hairHi: '#8d8178',
      beard: '#3a302b', beardHi: '#9a8f86', brow: '#2a201b',
      robe: '#3f5878', robeShade: '#2a3d57', robeLine: '#1f2c40',
      mantle: '#7b4e2c', mantleShade: '#56341b', trim: null,
      hairStyle: 'curly', beardStyle: 'short', eye: '#4a2e1a', age: 0.55, gray: 0.35,
    },
    john: {
      skin: '#dcae88', skinShade: '#b17d5a', lip: '#b06a5c',
      hair: '#6b3a22', hairShade: '#45230f', hairHi: '#9a5d38',
      beard: '#6b3a22', beardHi: '#9a5d38', brow: '#4f2a17',
      robe: '#6f7f4a', robeShade: '#4d5b30', robeLine: '#3a4524',
      mantle: '#c9b48c', mantleShade: '#9c8763', trim: null,
      hairStyle: 'wavy', beardStyle: 'light', eye: '#5b3a22', age: 0, young: true,
    },
    andrew: {
      skin: '#c48f69', skinShade: '#956042', lip: '#97584b',
      hair: '#3a2416', hairShade: '#22140b', hairHi: '#6b4a33',
      beard: '#33200f', beardHi: '#5e4128', brow: '#2a1a0e',
      robe: '#8b5a3a', robeShade: '#65402a', robeLine: '#4a2e1d',
      mantle: '#c7b08a', mantleShade: '#a08a64', trim: null,
      hairStyle: 'headcloth', cloth: '#d8c6a2', clothShade: '#b39e78', band: '#5a3a2a',
      beardStyle: 'full', eye: '#4a2e1a', age: 0.3,
    },
    thomas: {
      skin: '#b98260', skinShade: '#8a573a', lip: '#8e5146',
      hair: '#241812', hairShade: '#120b07', hairHi: '#4d382c',
      beard: '#20150f', beardHi: '#4d382c', brow: '#1d130c',
      robe: '#7a2e2e', robeShade: '#561f1f', robeLine: '#3e1515',
      mantle: '#5f6b4a', mantleShade: '#434d33', trim: null,
      hairStyle: 'short', beardStyle: 'full', eye: '#3e2516', age: 0.25,
    },
    matthew: {
      skin: '#cf9d78', skinShade: '#a06d4d', lip: '#a16053',
      hair: '#5a3c26', hairShade: '#3a2515', hairHi: '#8a6446',
      beard: '#4a3020', beardHi: '#7a5638', brow: '#3a2414',
      robe: '#4a5a6a', robeShade: '#33404d', robeLine: '#232d37',
      mantle: '#b8956a', mantleShade: '#8e6f4a', trim: null,
      hairStyle: 'headcloth', cloth: '#efe7d6', clothShade: '#cdbfa6', band: '#7a2f2f',
      beardStyle: 'short', eye: '#4a2e1a', age: 0.2,
    },
    james: {
      skin: '#c7946e', skinShade: '#986446', lip: '#98594c',
      hair: '#2c1c12', hairShade: '#180e08', hairHi: '#5a4030',
      beard: '#2c1c12', beardHi: '#5a4030', brow: '#22150c',
      robe: '#6a4a7a', robeShade: '#4b3358', robeLine: '#362440',
      mantle: '#a8865a', mantleShade: '#80643f', trim: null,
      hairStyle: 'curly', beardStyle: 'full', eye: '#3e2516', age: 0.25, gray: 0,
    },
  };

  // ---------------------------------------------------------------- helpers
  function inPoly(x, y, pts) {
    let c = false;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const [xi, yi] = pts[i], [xj, yj] = pts[j];
      if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
    }
    return c;
  }

  // Short hair strokes scattered inside a polygon (beard / hair texture).
  function strands(pts, n, seed, color, opacity, len, width, dirFn) {
    const r = rng(seed);
    let xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    let d = '', tries = 0, k = 0;
    while (k < n && tries < n * 30) {
      tries++;
      const x = lerp(x0, x1, r()), y = lerp(y0, y1, r());
      if (!inPoly(x, y, pts)) continue;
      const [dx, dy] = dirFn(x, y);
      const l = len * (0.6 + r() * 0.7);
      const bend = (r() - 0.5) * l * 0.5;
      d += `M${f(x)},${f(y)}q${f(dx * l * 0.5 - dy * bend)},${f(dy * l * 0.5 + dx * bend)} ${f(dx * l)},${f(dy * l)}`;
      k++;
    }
    return `<path d="${d}" fill="none" stroke="${color}" stroke-width="${width}" stroke-linecap="round" opacity="${opacity}"/>`;
  }

  function lg(id, stops, x1 = 0, y1 = 0, x2 = 1, y2 = 0) {
    return `<linearGradient id="${id}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}">` +
      stops.map(([o, c, a]) => `<stop offset="${o}" stop-color="${c}"${a !== undefined ? ` stop-opacity="${a}"` : ''}/>`).join('') +
      '</linearGradient>';
  }
  function rg(id, stops, cx = 0.5, cy = 0.5, r = 0.5) {
    return `<radialGradient id="${id}" cx="${cx}" cy="${cy}" r="${r}">` +
      stops.map(([o, c, a]) => `<stop offset="${o}" stop-color="${c}"${a !== undefined ? ` stop-opacity="${a}"` : ''}/>`).join('') +
      '</radialGradient>';
  }

  function defs(id, p, side) {
    const a = side < 0 ? 0 : 1, b = 1 - a;
    return '<defs>' +
      lg(`${id}-skin`, [[0, shade(p.skin, 0.07)], [0.5, p.skin], [1, p.skinShade]], a, 0, b, 0.15) +
      lg(`${id}-neck`, [[0, p.skinShade], [0.45, mix(p.skin, p.skinShade, 0.45)], [1, p.skinShade]], 0, 0, 0, 1) +
      lg(`${id}-hair`, [[0, p.hairHi || p.hair], [0.35, p.hair], [1, p.hairShade]], a, 0, b, 1) +
      lg(`${id}-hairB`, [[0, p.hair], [1, p.hairShade]], 0, 0, 0, 1) +
      lg(`${id}-beard`, [[0, p.beard], [0.7, shade(p.beard, -0.12)], [1, shade(p.beard, -0.3)]], 0, 0, 0, 1) +
      lg(`${id}-robe`, [[0, shade(p.robe, 0.06)], [0.55, p.robe], [1, p.robeShade]], a, 0, b, 0.3) +
      (p.mantle ? lg(`${id}-mantle`, [[0, shade(p.mantle, 0.08)], [0.5, p.mantle], [1, p.mantleShade]], a, 0, b, 0.2) : '') +
      (p.cloth ? lg(`${id}-cloth`, [[0, shade(p.cloth, 0.05)], [0.55, p.cloth], [1, p.clothShade]], a, 0, b, 0.3) : '') +
      rg(`${id}-cheek`, [[0, p.skinShade, 0.55], [1, p.skinShade, 0]]) +
      rg(`${id}-blush`, [[0, '#d0645a', 0.22], [1, '#d0645a', 0]]) +
      rg(`${id}-hi`, [[0, '#fff4e6', 0.32], [1, '#fff4e6', 0]]) +
      rg(`${id}-socket`, [[0, p.skinShade, 0.45], [1, p.skinShade, 0]]) +
      lg(`${id}-lidsh`, [[0, '#3a1c10', 0.5], [0.55, '#3a1c10', 0]], 0, 0, 0, 1) +
      rg(`${id}-iris`, [[0, shade(p.eye, 0.25)], [0.65, p.eye], [1, shade(p.eye, -0.45)]]) +
      '</defs>';
  }

  // ---------------------------------------------------------------- face parts
  function eye(id, cx, cy, side, w, open, lx, ly, p, heavy) {
    // side -1: viewer-left eye (outer corner left); +1: viewer-right eye
    const hw = 19 * w;
    const ox = cx + side * hw, ix = cx - side * (hw - 1);
    const oy = cy + 1.5, iy = cy + 2.2;
    if (open < 0.14) {
      // closed: soft downward arc + lashes
      const d = `M${f(ox)},${f(oy)} C${f(cx + side * hw * 0.45)},${f(cy + 6.5)} ${f(cx - side * hw * 0.4)},${f(cy + 6.8)} ${f(ix)},${f(iy + 0.5)}`;
      return `<path d="${d}" fill="none" stroke="${OUT}" stroke-width="3.1" stroke-linecap="round"/>` +
        `<path d="M${f(ox)},${f(oy)} l${f(side * 4)},${f(1.5)}" stroke="${OUT}" stroke-width="2.4" stroke-linecap="round"/>` +
        `<path d="M${f(cx + side * hw * 0.8)},${f(cy - 4)} C${f(cx + side * hw * 0.2)},${f(cy - 8)} ${f(cx - side * hw * 0.4)},${f(cy - 7)} ${f(ix + side * 2)},${f(cy - 3)}" fill="none" stroke="${p.skinShade}" stroke-width="1.4" opacity="0.7"/>`;
    }
    const top = cy - 11.8 * open;
    const upper = `M${f(ox)},${f(oy)} C${f(cx + side * hw * 0.55)},${f(top + 1.2)} ${f(cx - side * hw * 0.35)},${f(top - 0.4)} ${f(ix)},${f(iy)}`;
    const lowY = cy + 7 * Math.max(0.55, Math.min(open, 1));
    const lower = `C${f(cx - side * hw * 0.4)},${f(lowY)} ${f(cx + side * hw * 0.5)},${f(lowY + 0.6)} ${f(ox)},${f(oy)}Z`;
    const shape = upper + lower;
    const cid = `${id}-eye${side < 0 ? 'L' : 'R'}`;
    const irx = cx + lx * hw * 0.42, iry = cy + 0.4 + ly * (ly < 0 ? 5.4 : 3.8);
    const ir = 9.3 * Math.sqrt(w);
    let s = `<clipPath id="${cid}"><path d="${shape}"/></clipPath>`;
    s += `<path d="${shape}" fill="#f3ece3"/>`;
    s += `<g clip-path="url(#${cid})">` +
      `<circle cx="${f(irx)}" cy="${f(iry)}" r="${f(ir)}" fill="url(#${id}-iris)"/>` +
      `<circle cx="${f(irx)}" cy="${f(iry)}" r="${f(ir)}" fill="none" stroke="#1a0e08" stroke-width="1.1" opacity="0.7"/>` +
      `<circle cx="${f(irx)}" cy="${f(iry + 0.3)}" r="${f(ir * 0.46)}" fill="#120a06"/>` +
      `<circle cx="${f(irx + 2.8)}" cy="${f(iry - 3)}" r="2.5" fill="#ffffff"/>` +
      `<circle cx="${f(irx - 2.6)}" cy="${f(iry + 2.8)}" r="1.1" fill="#ffffff" opacity="0.8"/>` +
      `<rect x="${f(cx - hw - 4)}" y="${f(top - 2)}" width="${f(hw * 2 + 8)}" height="${f(14)}" fill="url(#${id}-lidsh)"/>` +
      '</g>';
    // upper lid line, thicker toward the outer corner, with a small flick
    s += `<path d="${upper}" fill="none" stroke="${OUT}" stroke-width="${f(3.2 + heavy * 0.8)}" stroke-linecap="round"/>`;
    s += `<path d="M${f(ox + side * 0.5)},${f(oy - 0.5)} l${f(side * 4.2)},${f(-2.4)}" stroke="${OUT}" stroke-width="2.3" stroke-linecap="round"/>`;
    // crease
    s += `<path d="M${f(cx + side * hw * 0.85)},${f(top + 3)} C${f(cx + side * hw * 0.35)},${f(top - 4.5)} ${f(cx - side * hw * 0.35)},${f(top - 4.8)} ${f(ix + side * 1.5)},${f(top + 1.5)}" fill="none" stroke="${p.skinShade}" stroke-width="1.5" opacity="0.75" stroke-linecap="round"/>`;
    // lower lid
    s += `<path d="M${f(ox - side * 2)},${f(oy + 1.5)} C${f(cx + side * hw * 0.4)},${f(lowY + 1.2)} ${f(cx - side * hw * 0.25)},${f(lowY + 1.4)} ${f(ix + side * 4)},${f(iy + 2.5)}" fill="none" stroke="${shade(p.skinShade, -0.15)}" stroke-width="1.2" opacity="0.55" stroke-linecap="round"/>`;
    return s;
  }

  function brow(cx, cy, side, raise, sad, color, w) {
    const ox = cx + side * 22 * w, ix = cx - side * 16;
    const inY = cy - 1 - sad * 5.5 - raise * 4.5, outY = cy + 3.5 - raise * 5 + sad * 2.5;
    const d = `M${f(ox)},${f(outY)} C${f(ox - side * 9)},${f(outY - 7.5)} ${f(ix + side * 10)},${f(inY - 6.5)} ${f(ix)},${f(inY - 3.2)}` +
      `L${f(ix - side * 1.2)},${f(inY + 3.6)} C${f(ix + side * 10)},${f(inY - 0.4)} ${f(ox - side * 9)},${f(outY - 2)} ${f(ox)},${f(outY + 1.2)}Z`;
    return `<path d="${d}" fill="${color}"/>`;
  }

  // jaw: 'male' (long, hidden by a beard), 'young' (shorter, softer), 'female', 'child'
  const JAW = { male: [127, 60, 48, 24], young: [116, 62, 50, 30], female: [112, 60, 46, 26], child: [104, 64, 54, 34] };
  function faceOutline(turn, jaw = 'male') {
    const [cy, j1, j2, j3] = JAW[jaw] || JAW.male;
    const a = 1 - Math.max(0, turn) * 0.06, b = 1 - Math.max(0, -turn) * 0.06;
    const L = (x) => x * b, R = (x) => x * a;
    const k = (cy - 20) / 107;
    return `M${f(L(-70))},-50 C${f(L(-73))},-5 ${f(L(-71))},35 ${f(L(-j1))},${f(20 + 45 * k)} C${f(L(-j2))},${f(20 + 78 * k)} ${f(L(-j3) + turn * 6)},${f(cy - 3)} ${f(turn * 8)},${cy} ` +
      `C${f(R(j3) + turn * 6)},${f(cy - 3)} ${f(R(j2))},${f(20 + 78 * k)} ${f(R(j1))},${f(20 + 45 * k)} C${f(R(71))},35 ${f(R(73))},-5 ${f(R(70))},-50 ` +
      `C${f(R(66))},-102 ${f(R(36))},-131 0,-131 C${f(L(-36))},-131 ${f(L(-66))},-102 ${f(L(-70))},-50Z`;
  }

  function ear(side, p, turn) {
    if (side * turn > 0.25) return '';
    const x = side * 70;
    const d = `M${f(x)},-12 C${f(x + side * 13)},-20 ${f(x + side * 17)},2 ${f(x + side * 13)},20 C${f(x + side * 10)},32 ${f(x + side * 4)},38 ${f(x - side * 1)},34Z`;
    return `<path d="${d}" fill="${mix(p.skin, p.skinShade, 0.35)}" stroke="${OUT}" stroke-width="1.6"/>` +
      `<path d="M${f(x + side * 4)},-6 C${f(x + side * 11)},-6 ${f(x + side * 11)},14 ${f(x + side * 5)},22" fill="none" stroke="${p.skinShade}" stroke-width="1.6" opacity="0.8"/>`;
  }

  function nose(nx, p, side, turn) {
    // side: which side the shadow falls (opposite the key light)
    const sx = nx + side * 7;
    let s = `<path d="M${f(sx - side * 2)},-16 C${f(sx + side * 1)},0 ${f(sx + side * 2)},18 ${f(sx + side * 4)},34" fill="none" stroke="${p.skinShade}" stroke-width="2.6" opacity="0.55" stroke-linecap="round"/>`;
    s += `<path d="M${f(nx - side * 5)},-10 C${f(nx - side * 4)},6 ${f(nx - side * 3)},20 ${f(nx - side * 2)},30" fill="none" stroke="#fff3e2" stroke-width="2.2" opacity="0.22" stroke-linecap="round"/>`;
    s += `<ellipse cx="${f(nx + side * 3)}" cy="51" rx="13" ry="4" fill="${p.skinShade}" opacity="0.35"/>`;
    s += `<path d="M${f(nx - 9)},43 C${f(nx - 5)},48.5 ${f(nx + 5)},48.5 ${f(nx + 9)},43" fill="none" stroke="${shade(p.skinShade, -0.25)}" stroke-width="1.7" stroke-linecap="round"/>`;
    s += `<path d="M${f(nx - 13)},37 C${f(nx - 16.5)},42.5 ${f(nx - 13.5)},47 ${f(nx - 8.5)},46" fill="none" stroke="${shade(p.skinShade, -0.2)}" stroke-width="1.6" stroke-linecap="round" opacity="0.85"/>`;
    s += `<path d="M${f(nx + 13)},37 C${f(nx + 16.5)},42.5 ${f(nx + 13.5)},47 ${f(nx + 8.5)},46" fill="none" stroke="${shade(p.skinShade, -0.2)}" stroke-width="1.6" stroke-linecap="round" opacity="0.85"/>`;
    return s;
  }

  function mouth(mx, open, smile, p, hasStache) {
    const y = 78;
    const h = 1.2 + open * 11, w = 13 - open * 2.2;
    const cy = y - smile * 2.5;
    let s = '';
    if (open > 0.06) {
      const d = `M${f(mx - w)},${f(cy)} C${f(mx - w * 0.5)},${f(y - 1.6)} ${f(mx + w * 0.5)},${f(y - 1.6)} ${f(mx + w)},${f(cy)} C${f(mx + w * 0.6)},${f(y + h)} ${f(mx - w * 0.6)},${f(y + h)} ${f(mx - w)},${f(cy)}Z`;
      s += `<path d="${d}" fill="#3a1411"/>`;
      if (open > 0.3) s += `<path d="M${f(mx - w * 0.7)},${f(y - 0.6)} C${f(mx - w * 0.3)},${f(y + 2.2)} ${f(mx + w * 0.3)},${f(y + 2.2)} ${f(mx + w * 0.7)},${f(y - 0.6)}Z" fill="#efe8de" opacity="0.92"/>`;
      if (open > 0.55) s += `<ellipse cx="${f(mx)}" cy="${f(y + h * 0.72)}" rx="${f(w * 0.45)}" ry="${f(h * 0.2)}" fill="#8f3b3a" opacity="0.8"/>`;
    } else {
      s += `<path d="M${f(mx - w)},${f(cy)} C${f(mx - w * 0.4)},${f(y + 1)} ${f(mx + w * 0.4)},${f(y + 1)} ${f(mx + w)},${f(cy)}" fill="none" stroke="#4a1f18" stroke-width="2" stroke-linecap="round"/>`;
    }
    // lower lip
    const ly = y + Math.max(h, 1.5) + 0.5;
    s += `<path d="M${f(mx - w * 0.75)},${f(ly - 1)} C${f(mx - w * 0.5)},${f(ly + 6)} ${f(mx + w * 0.5)},${f(ly + 6)} ${f(mx + w * 0.75)},${f(ly - 1)} C${f(mx + w * 0.3)},${f(ly + 1)} ${f(mx - w * 0.3)},${f(ly + 1)} ${f(mx - w * 0.75)},${f(ly - 1)}Z" fill="${p.lip}"/>`;
    s += `<path d="M${f(mx - w * 0.3)},${f(ly + 2.2)} Q${f(mx)},${f(ly + 3.6)} ${f(mx + w * 0.3)},${f(ly + 2.2)}" fill="none" stroke="#ffffff" stroke-width="1.2" opacity="0.25" stroke-linecap="round"/>`;
    if (!hasStache) {
      s += `<path d="M${f(mx - w * 0.85)},${f(cy - 0.5)} C${f(mx - w * 0.4)},${f(y - 5)} ${f(mx + w * 0.4)},${f(y - 5)} ${f(mx + w * 0.85)},${f(cy - 0.5)}Z" fill="${mix(p.lip, p.skinShade, 0.4)}" opacity="0.9"/>`;
    }
    return s;
  }

  function mustache(mx, p, id, seed, scale = 1) {
    const pts = [[0, 60], [-12, 57.5], [-24, 62], [-31, 72], [-34.5, 86], [-33, 94], [-27, 83], [-17, 76.6], [-6, 74.6], [0, 75.2], [6, 74.6], [17, 76.6], [27, 83], [33, 94], [34.5, 86], [31, 72], [24, 62], [12, 57.5]]
      .map(([x, y]) => [mx + x * scale, 60 + (y - 60) * scale]);
    const edge = tufts(pts.concat([pts[0]]), 1.6, 5, seed, 0.4);
    let s = `<path d="${spline(edge, true, 0.35)}" fill="${p.beard}"/>`;
    s += strands(pts, 18, seed + 3, p.beardHi, 0.45, 9, 1.2, (x) => [x < mx ? -0.7 : 0.7, 0.7]);
    return s;
  }

  function beardShape(style, tx, turn) {
    // returns outer polygon points (closed) for the beard region
    const near = 1 + Math.abs(turn) * 0.04;
    if (style === 'full' || style === 'long') {
      const drop = style === 'long' ? 70 : 0;
      const outerL = [[-71, -14], [-72.5, 22], [-68, 58], [-58, 92], [-43, 121 + drop * 0.4], [-23, 141 + drop * 0.85], [0, 150 + drop]];
      const outerR = outerL.slice(0, -1).reverse().map(([x, y]) => [-x, y]);
      const inner = [[66, -14], [63, 10], [56, 32], [44, 50], [29, 61], [12, 61.5], [0, 61], [-12, 61.5], [-29, 61], [-44, 50], [-56, 32], [-63, 10], [-66, -14]];
      const sh = (pt, k) => [pt[0] * near + tx * k, pt[1]];
      return { outer: outerL.concat(outerR).map((pt) => sh(pt, 0.55)), inner: inner.map((pt) => sh(pt, 1)) };
    }
    if (style === 'short') {
      const outerL = [[-70, -12], [-71.5, 26], [-66, 60], [-55, 90], [-40, 113], [-21, 128], [0, 133]];
      const outerR = outerL.slice(0, -1).reverse().map(([x, y]) => [-x, y]);
      const inner = [[62, -10], [60, 18], [53, 42], [40, 58], [27, 64], [12, 62], [0, 61.5], [-12, 62], [-27, 64], [-40, 58], [-53, 42], [-60, 18], [-62, -10]];
      const sh = (pt, k) => [pt[0] * near + tx * k, pt[1]];
      return { outer: outerL.concat(outerR).map((pt) => sh(pt, 0.55)), inner: inner.map((pt) => sh(pt, 1)) };
    }
    return null;
  }

  function beard(style, p, id, tx, turn, seed) {
    if (style === 'none') return '';
    if (style === 'stubble') {
      const sh = beardShape('short', tx, turn);
      const pts = sh.outer.concat(sh.inner);
      return `<path d="${spline(pts, true, 0.4)}" fill="${p.beard}" opacity="0.16"/>`;
    }
    const sh = beardShape(style, tx, turn);
    const outer = tufts(sh.outer, style === 'short' ? 2.6 : 3.4, 9, seed, 0.5);
    const inner = tufts(sh.inner, 0.9, 9, seed + 1, 0.4);
    const pts = outer.concat(inner);
    const region = sh.outer.concat(sh.inner);
    let s = `<path d="${spline(pts, true, 0.42)}" fill="url(#${id}-beard)"/>`;
    s += `<path d="${spline(outer.slice(4, -4), false, 0.42)}" fill="none" stroke="${shade(p.beard, -0.45)}" stroke-width="1.4" opacity="0.7"/>`;
    s += strands(region, style === 'short' ? 22 : 30, seed + 7, p.beardHi, 0.3, 12, 1.4, (x, y) => {
      const a = Math.atan2(y + 20, x - tx); return [Math.cos(a) * 0.45, Math.abs(Math.sin(a)) * 0.9 + 0.3];
    });
    s += strands(region, 16, seed + 9, shade(p.beard, -0.4), 0.35, 12, 1.3, (x, y) => [x > tx ? 0.3 : -0.3, 1]);
    // soft highlight on the upper beard where the lamp light catches it
    s += `<path d="${spline(sh.inner.map(([x, y]) => [x * 0.9 + tx * 0.1, y + 18]), false)}" fill="none" stroke="${p.beardHi}" stroke-width="6" opacity="0.18" stroke-linecap="round"/>`;
    return s;
  }

  // ---------------------------------------------------------------- hair
  function hairBack(style, p, id) {
    if (style === 'long') {
      const pts = [[0, -150], [-66, -136], [-108, -88], [-120, -10], [-122, 80], [-128, 180], [-138, 270], [-120, 300], [-80, 300], [-64, 240], [-56, 180], [-42, 120], [0, 112], [42, 120], [56, 180], [64, 240], [80, 300], [120, 300], [138, 270], [128, 180], [122, 80], [120, -10], [108, -88], [66, -136]];
      return `<path d="${spline(pts, true)}" fill="url(#${id}-hairB)" stroke="${OUT}" stroke-width="2"/>`;
    }
    if (style === 'veil' || style === 'headcloth') {
      const c = style === 'veil' ? p.veil : p.cloth;
      const cs = style === 'veil' ? p.veilShade : p.clothShade;
      const pts = [[0, -158], [-72, -140], [-104, -86], [-114, -10], [-118, 80], [-126, 170], [-150, 230], [-120, 250], [-70, 236], [-50, 160], [0, 140], [50, 160], [70, 236], [120, 250], [150, 230], [126, 170], [118, 80], [114, -10], [104, -86], [72, -140]];
      return `<path d="${spline(pts, true)}" fill="${shade(cs, -0.08)}" stroke="${OUT}" stroke-width="2"/>`;
    }
    if (style === 'longFemale') {
      const pts = [[0, -146], [-66, -128], [-100, -80], [-110, -10], [-112, 80], [-120, 170], [-112, 230], [-70, 236], [-54, 170], [0, 130], [54, 170], [70, 236], [112, 230], [120, 170], [112, 80], [110, -10], [100, -80], [66, -128]];
      return `<path d="${spline(pts, true)}" fill="url(#${id}-hairB)" stroke="${OUT}" stroke-width="2"/>`;
    }
    return '';
  }

  function hairFront(style, p, id, seed, tx) {
    let s = '';
    if (style === 'long') {
      // Two curtains from a centre part: over the crown, past the temples (overlapping the
      // face edge a little) and down over the shoulders, ending in wavy strand clusters.
      const r = rng(seed);
      for (const sg of [-1, 1]) {
        const j = (k) => k + (r() - 0.5) * 8;
        const pts = [
          [sg * 3, -146], [sg * 46, -144], [sg * 84, -122], [sg * 103, -80], [sg * 106, -30], [sg * 112, 14], [sg * 107, 60],
          [sg * 114, 108], [sg * 124, 160], [sg * 130, 214],
          [sg * 128, j(262)], [sg * 116, j(250)], [sg * 104, j(274)], [sg * 92, j(246)], [sg * 82, j(258)],
          [sg * 77, 200], [sg * 75, 130], [sg * 74, 64], [sg * 73, 4], [sg * 70, -36], [sg * 63, -60],
          [sg * 48, -78], [sg * 28, -91], [sg * 12, -98], [sg * 3, -100],
        ];
        s += `<path d="${spline(pts, true, 0.45)}" fill="url(#${id}-hair)" stroke="${OUT}" stroke-width="2.2" stroke-linejoin="round"/>`;
        // strands: flow from the part over the crown and down the curtain
        let d = '', dh = '';
        for (let i = 0; i < 8; i++) {
          const u = i / 7;
          const x0 = sg * (8 + u * 30), y0 = -140 + u * 22;
          const xm = sg * (78 + u * 26), xe = sg * (82 + u * 40 + r() * 6);
          d += `M${f(x0)},${f(y0)} C${f(sg * (50 + u * 30))},${f(-136 + u * 20)} ${f(xm)},${f(-96 + u * 10)} ${f(sg * (80 + u * 24))},${f(-20 + u * 10)} ` +
            `S${f(xe - sg * 10)},${f(140 + r() * 30)} ${f(xe)},${f(210 + r() * 40)}`;
        }
        for (let i = 0; i < 4; i++) {
          const x0 = sg * (14 + i * 10);
          dh += `M${f(x0)},${f(-140 + i * 3)} C${f(sg * (44 + i * 10))},${f(-134 + i * 3)} ${f(sg * (72 + i * 8))},${f(-108 + i * 4)} ${f(sg * (88 + i * 6))},${f(-60 + i * 10)}`;
        }
        s += `<path d="${d}" fill="none" stroke="${p.hairShade}" stroke-width="1.6" opacity="0.75"/>`;
        s += `<path d="${dh}" fill="none" stroke="${p.hairHi}" stroke-width="2.4" opacity="0.55" stroke-linecap="round"/>`;
      }
      s += `<path d="M0,-147 C0,-132 1,-120 2,-110" fill="none" stroke="${p.hairShade}" stroke-width="2.4" opacity="0.9"/>`;
      return s;
    }
    if (style === 'curly') {
      const cap = [[-74, -20], [-80, -60], [-70, -104], [-44, -134], [-6, -146], [34, -142], [64, -120], [80, -82], [78, -36], [74, -18], [64, -54], [50, -80], [20, -96], [-10, -98], [-40, -90], [-60, -66], [-68, -38]];
      const edge = tufts(cap.concat([cap[0]]), 6, 10, seed, 0.2);
      s += `<path d="${spline(edge, true, 0.55)}" fill="url(#${id}-hair)" stroke="${OUT}" stroke-width="2"/>`;
      const r = rng(seed + 5);
      let d = '', g = '';
      for (let i = 0; i < 34; i++) {
        const a = Math.PI * (1.05 + r() * 0.9), rad = 70 + r() * 50;
        const x = Math.cos(a) * rad * 0.85, y = -40 + Math.sin(a) * rad * 0.9;
        if (y > -50 && Math.abs(x) < 55) continue;
        const k = 6 + r() * 5;
        const arc = `M${f(x - k)},${f(y)} a${f(k)},${f(k * 0.8)} 0 1 1 ${f(k * 1.6)},${f(1)}`;
        if (r() < (p.gray || 0)) g += arc; else d += arc;
      }
      s += `<path d="${d}" fill="none" stroke="${p.hairShade}" stroke-width="1.8" opacity="0.75"/>`;
      if (g) s += `<path d="${g}" fill="none" stroke="${p.hairHi}" stroke-width="2" opacity="0.8"/>`;
      return s;
    }
    if (style === 'wavy' || style === 'short') {
      const fr = style === 'wavy' ? 1 : 0.4;
      const cap = [[-73, -24], [-80, -70], [-62, -114], [-26, -140], [16, -142], [56, -124], [78, -88], [80, -46], [74, -20], [66, -50], [52, -76], [30, -88 + 6 * fr], [8, -86 + 10 * fr], [-14, -92 + 8 * fr], [-34, -84 + 8 * fr], [-52, -78], [-66, -52]];
      const edge = tufts(cap.concat([cap[0]]), 2.6, 9, seed, 0.3);
      s += `<path d="${spline(edge, true, 0.5)}" fill="url(#${id}-hair)" stroke="${OUT}" stroke-width="2"/>`;
      let d = '';
      for (let i = 0; i < 6; i++) {
        const x = -50 + i * 20;
        d += `M${f(x)},${f(-130 + Math.abs(x) * 0.25)} C${f(x + 14)},-118 ${f(x + 10)},-100 ${f(x + 22)},${f(-88 + (i % 2) * 6)}`;
      }
      s += `<path d="${d}" fill="none" stroke="${p.hairShade}" stroke-width="1.7" opacity="0.7"/>`;
      s += `<path d="M-40,-128 C-14,-138 18,-136 40,-124" fill="none" stroke="${p.hairHi}" stroke-width="3" opacity="0.45" stroke-linecap="round"/>`;
      return s;
    }
    if (style === 'headcloth' || style === 'veil') {
      const c = style === 'veil' ? p.veil : p.cloth;
      const cid = style === 'veil' ? `${id}-veil` : `${id}-cloth`;
      const pts = [[-2, -160], [-50, -152], [-88, -112], [-92, -60], [-88, 0], [-90, 70], [-100, 140], [-128, 214], [-96, 226], [-74, 170], [-72, 90], [-74, 20], [-74, -40], [-66, -84], [-40, -100], [0, -104], [40, -100], [66, -84], [74, -40], [74, 20], [72, 90], [74, 170], [96, 226], [128, 214], [100, 140], [90, 70], [88, 0], [92, -60], [88, -112], [50, -152]];
      s += `<path d="${spline(pts, true)}" fill="${style === 'veil' ? c : `url(#${cid})`}" stroke="${OUT}" stroke-width="2.2"/>`;
      s += `<path d="M-80,-70 C-84,0 -84,80 -96,170 M80,-70 C84,0 84,80 96,170 M-40,-140 C-60,-120 -76,-90 -80,-50 M40,-140 C60,-120 76,-90 80,-50" fill="none" stroke="${p.clothShade || p.veilShade}" stroke-width="2" opacity="0.8"/>`;
      if (style === 'headcloth') {
        s += `<path d="M-74,-82 C-40,-102 40,-102 74,-82 L74,-70 C40,-90 -40,-90 -74,-70Z" fill="${p.band}" stroke="${OUT}" stroke-width="1.6"/>`;
        s += `<path d="M-70,-78 C-36,-96 36,-96 70,-78" fill="none" stroke="${shade(p.band, 0.25)}" stroke-width="1.4" opacity="0.7"/>`;
      }
      return s;
    }
    if (style === 'longFemale') {
      const cap = [[-72, -10], [-80, -70], [-60, -118], [-20, -142], [24, -142], [62, -118], [80, -70], [72, -10], [66, -60], [44, -96], [10, -106], [-24, -102], [-50, -84], [-66, -50]];
      s += `<path d="${spline(cap, true)}" fill="url(#${id}-hair)" stroke="${OUT}" stroke-width="2"/>`;
      s += `<path d="M-30,-130 C-50,-110 -66,-70 -70,-20 M30,-130 C50,-110 66,-70 70,-20" fill="none" stroke="${p.hairShade}" stroke-width="1.8" opacity="0.7"/>`;
      return s;
    }
    return s;
  }

  // ---------------------------------------------------------------- body & hands
  function hand(kind, x, y, rot, sc, flip, p) {
    const t = `translate(${f(x)},${f(y)}) rotate(${f(rot)}) scale(${f(sc * (flip ? -1 : 1))},${f(sc)})`;
    const fill = mix(p.skin, p.skinShade, 0.15), line = shade(p.skinShade, -0.25);
    let d = '';
    if (kind === 'fist') {
      d = `<path d="M-30,-14 C-30,-28 -10,-34 8,-32 C26,-30 36,-20 36,-4 C36,12 28,24 10,26 C-8,28 -26,22 -30,6Z" fill="${fill}" stroke="${OUT}" stroke-width="2"/>` +
        `<path d="M18,-30 C26,-26 30,-18 30,-10 M24,-14 C32,-8 34,0 32,8 M24,6 C30,12 30,18 26,22" fill="none" stroke="${line}" stroke-width="1.5" opacity="0.75" stroke-linecap="round"/>` +
        `<path d="M-30,-10 C-38,-20 -34,-34 -20,-34 C-10,-33 -4,-26 -6,-18" fill="${fill}" stroke="${OUT}" stroke-width="1.8"/>`;
    } else if (kind === 'hold') {
      // back of the hand with fingers draped forward (+x) over an object
      d = `<path d="M-30,-14 C-26,-26 -6,-30 10,-28 C24,-27 36,-24 46,-18 C54,-13 54,-4 48,0 C55,4 54,13 47,15 C51,21 47,28 39,26 C28,24 16,22 6,22 C-10,24 -26,18 -30,4Z" fill="${fill}" stroke="${OUT}" stroke-width="2" stroke-linejoin="round"/>` +
        `<path d="M14,-26 C26,-20 38,-14 47,-8 M14,-10 C26,-6 38,-2 48,2 M12,6 C24,8 34,12 44,15" fill="none" stroke="${line}" stroke-width="1.5" opacity="0.7" stroke-linecap="round"/>` +
        `<path d="M-14,-22 C-6,-24 2,-24 8,-22" fill="none" stroke="#fff3e2" stroke-width="2" opacity="0.3" stroke-linecap="round"/>`;
    } else if (kind === 'open') {
      // palm up, fingers pointing outward (+x)
      d = `<path d="M-30,-6 C-30,-22 -8,-26 10,-24 L44,-26 C52,-26 54,-18 46,-16 L16,-14 L50,-14 C58,-13 58,-4 50,-4 L18,-4 L48,4 C55,6 54,14 46,13 L16,8 L40,16 C46,19 44,26 37,24 L10,18 C-6,22 -26,18 -30,-6Z" fill="${fill}" stroke="${OUT}" stroke-width="2" stroke-linejoin="round"/>` +
        `<path d="M-30,-8 C-40,-20 -38,-34 -24,-34 C-14,-33 -8,-26 -6,-20" fill="${fill}" stroke="${OUT}" stroke-width="1.8"/>` +
        `<path d="M-14,0 C-4,4 6,2 12,-4" fill="none" stroke="${line}" stroke-width="1.4" opacity="0.6"/>`;
    } else if (kind === 'flat') {
      // praying palm, seen from the side, fingers up
      d = `<path d="M-14,40 C-18,10 -16,-20 -10,-46 C-6,-62 6,-62 8,-46 C10,-20 12,10 10,40 C6,50 -10,50 -14,40Z" fill="${fill}" stroke="${OUT}" stroke-width="2"/>` +
        `<path d="M-6,-40 L-4,10 M2,-44 L3,6" fill="none" stroke="${line}" stroke-width="1.3" opacity="0.6"/>`;
    } else if (kind === 'rest') {
      // relaxed hand seen from above resting on a table
      d = `<path d="M-30,-14 C-26,-26 10,-28 28,-22 C40,-18 42,-6 36,2 C30,10 6,14 -14,12 C-28,10 -34,0 -30,-14Z" fill="${fill}" stroke="${OUT}" stroke-width="2"/>` +
        `<path d="M8,-22 C14,-12 16,0 14,10 M20,-20 C26,-12 28,-2 26,6 M-4,-24 C2,-14 2,0 0,12" fill="none" stroke="${line}" stroke-width="1.4" opacity="0.65"/>`;
    }
    return `<g transform="${t}">${d}</g>`;
  }

  function bread(x, y, sc) {
    return `<g transform="translate(${f(x)},${f(y)}) scale(${f(sc)})">` +
      `<ellipse cx="0" cy="6" rx="98" ry="52" fill="#7a4a22" stroke="${OUT}" stroke-width="2.4"/>` +
      `<path d="M-98,6 C-96,-46 -40,-62 0,-62 C40,-62 96,-46 98,6 C80,28 -80,28 -98,6Z" fill="#c98a45" stroke="${OUT}" stroke-width="2.4"/>` +
      `<path d="M-70,-14 C-60,-40 30,-56 70,-26" fill="none" stroke="#e8b673" stroke-width="10" opacity="0.6" stroke-linecap="round"/>` +
      `<path d="M-50,-8 C-44,-24 -30,-34 -18,-38 M-14,-4 C-8,-22 6,-34 18,-38 M22,-6 C28,-22 40,-30 52,-32" fill="none" stroke="#f6dcae" stroke-width="7" stroke-linecap="round"/>` +
      `<path d="M-50,-8 C-44,-24 -30,-34 -18,-38 M-14,-4 C-8,-22 6,-34 18,-38 M22,-6 C28,-22 40,-30 52,-32" fill="none" stroke="#9a5d28" stroke-width="2" stroke-linecap="round" opacity="0.6"/>` +
      `<circle cx="-30" cy="-30" r="1.6" fill="#fff4dc"/><circle cx="10" cy="-44" r="1.4" fill="#fff4dc"/><circle cx="44" cy="-20" r="1.5" fill="#fff4dc"/><circle cx="-6" cy="-20" r="1.2" fill="#fff4dc"/>` +
      '</g>';
  }

  function torso(p, id, o) {
    const pose = o.pose || 'rest';
    let s = '';
    const bodyD = pose === 'open'
      ? 'M-46,168 C-92,174 -136,190 -156,216 C-170,236 -174,270 -170,320 L-180,1700 L180,1700 L170,320 C174,270 170,236 156,216 C136,190 92,174 46,168Z'
      : 'M-46,168 C-92,174 -138,190 -160,218 C-178,244 -184,290 -186,350 L-198,1700 L198,1700 L186,350 C184,290 178,244 160,218 C138,190 92,174 46,168Z';
    s += `<path d="${bodyD}" fill="url(#${id}-robe)" stroke="${OUT}" stroke-width="2.4" stroke-linejoin="round"/>`;
    // chest skin inside V-neck
    s += `<path d="M-40,168 L0,${pose === 'open' ? 262 : 268} L40,168Z" fill="url(#${id}-neck)"/>`;
    s += `<path d="M-40,168 L0,268 L40,168" fill="none" stroke="${OUT}" stroke-width="2.2" stroke-linejoin="round"/>`;
    s += `<path d="M-34,176 L0,258" stroke="${p.robeLine}" stroke-width="2" opacity="0.6"/>`;
    // fold lines
    s += `<path d="M-118,300 C-110,400 -120,540 -112,760 L-116,1700 M-64,330 C-56,430 -66,580 -58,760 L-62,1700 M-150,250 C-140,320 -146,400 -140,470 M110,330 C104,430 114,560 106,760 L110,1700" fill="none" stroke="${p.robeLine}" stroke-width="2.2" opacity="0.45" stroke-linecap="round"/>`;
    if (pose !== 'open') {
      s += `<path d="M-132,290 C-128,400 -132,560 -128,780 L-130,1700 M132,290 C128,400 132,560 128,780 L130,1700" fill="none" stroke="${OUT}" stroke-width="1.8" opacity="0.55"/>`;
    }
    // mantle over the viewer-right shoulder (Jesus' left)
    if (p.mantle) {
      const m = 'M34,170 C90,176 142,194 164,222 C182,250 188,300 190,360 L198,1700 L76,1700 L72,780 C76,650 74,520 64,420 C56,340 46,256 34,170Z';
      s += `<path d="${m}" fill="url(#${id}-mantle)" stroke="${OUT}" stroke-width="2.4" stroke-linejoin="round"/>`;
      s += `<path d="M150,250 C160,340 158,460 168,620 L172,1700 M110,300 C118,420 112,560 120,760 L124,1700" fill="none" stroke="${p.mantleShade}" stroke-width="2.4" opacity="0.7"/>`;
      if (p.trim) {
        s += `<path d="M34,170 C46,256 56,340 64,420 C74,520 76,650 72,780 L76,1700" fill="none" stroke="${p.trim}" stroke-width="5.5"/>`;
        s += `<path d="M40,172 C52,256 62,340 70,420 C80,520 82,650 78,780 L82,1700" fill="none" stroke="${shade(p.trim, -0.35)}" stroke-width="1.4" opacity="0.8"/>`;
      }
    }
    return s;
  }

  const P = (a) => `${f(a[0])},${f(a[1])}`;

  // A sleeve segment from a (elbow/shoulder) to b (wrist), widths wa/wb, with a cuff opening at b.
  function sleeve(a, b, wa, wb, fill, p, cuff = true, sag = 0) {
    const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
    const ux = dx / L, uy = dy / L, px = -uy, py = ux;
    const a1 = [a[0] + (px * wa) / 2, a[1] + (py * wa) / 2], a2 = [a[0] - (px * wa) / 2, a[1] - (py * wa) / 2];
    const b1 = [b[0] + (px * wb) / 2, b[1] + (py * wb) / 2], b2 = [b[0] - (px * wb) / 2, b[1] - (py * wb) / 2];
    const at = (q, k, s2 = 0) => [q[0] + ux * L * k + px * s2, q[1] + uy * L * k + py * s2];
    const back = [a[0] - ux * wa * 0.45, a[1] - uy * wa * 0.45];
    const d = `M${P(a1)} C${P(at(a1, 0.35, sag))} ${P(at(b1, -0.3, sag))} ${P(b1)} L${P(b2)} C${P(at(b2, -0.3, sag))} ${P(at(a2, 0.35, sag))} ${P(a2)} Q${P(back)} ${P(a1)}Z`;
    let s = `<path d="${d}" fill="${fill}" stroke="${OUT}" stroke-width="2.4" stroke-linejoin="round"/>`;
    const m1 = at([a[0] + px * wa * 0.18, a[1] + py * wa * 0.18], 0.2), m2 = at([b[0] + px * wb * 0.12, b[1] + py * wb * 0.12], -0.12);
    const n1 = at([a[0] - px * wa * 0.2, a[1] - py * wa * 0.2], 0.35), n2 = at([b[0] - px * wb * 0.22, b[1] - py * wb * 0.22], -0.2);
    s += `<path d="M${P(m1)} L${P(m2)} M${P(n1)} L${P(n2)}" stroke="${p.robeLine}" stroke-width="2" opacity="0.5" stroke-linecap="round"/>`;
    if (cuff) {
      const ang = (Math.atan2(py, px) * 180) / Math.PI;
      s += `<ellipse cx="${f(b[0])}" cy="${f(b[1])}" rx="${f(wb / 2)}" ry="${f(wb * 0.13)}" transform="rotate(${f(ang)},${f(b[0])},${f(b[1])})" fill="${mix(p.robeShade, '#3a2010', 0.22)}" stroke="${OUT}" stroke-width="2"/>`;
    }
    return s;
  }

  function arms(p, id, o) {
    const pose = o.pose || 'rest';
    let back = '', front = '';
    const robeFill = `url(#${id}-robe)`;
    if (pose === 'table' || pose === 'bread') {
      if (pose === 'bread') {
        front += sleeve([-184, 420], [-122, 458], 76, 52, robeFill, p, true, -6) + sleeve([184, 420], [122, 458], 76, 52, robeFill, p, true, 6);
        front += bread(0, 520, 0.92);
        front += hand('hold', -96, 473, 30, 1, false, p) + hand('hold', 96, 473, -30, 1, true, p);
      } else {
        front += sleeve([-180, 470], [-86, 588], 84, 58, robeFill, p) + sleeve([180, 470], [86, 588], 84, 58, robeFill, p);
        front += hand('rest', -56, 600, 22, 1, false, p) + hand('rest', 56, 600, -22, 1, true, p);
      }
    } else if (pose === 'pray') {
      front += sleeve([-166, 566], [-22, 500], 86, 54, robeFill, p, true, -6) + sleeve([166, 566], [22, 500], 86, 54, robeFill, p, true, 6);
      front += hand('flat', -8, 438, 5, 1.05, false, p) + hand('flat', 8, 438, -5, 1.05, true, p);
      front += `<path d="M0,384 L0,482" stroke="${shade(p.skinShade, -0.2)}" stroke-width="1.6" opacity="0.7"/>`;
    } else if (pose === 'open') {
      for (const sg of [-1, 1]) {
        back += sleeve([sg * 146, 236], [sg * 214, 410], 80, 86, robeFill, p, false, sg * 8);
        back += sleeve([sg * 210, 404], [sg * 268, 548], 90, 76, robeFill, p, true, sg * 6);
        front += hand('open', sg * 300, 540, sg > 0 ? -28 : 28, 1.05, sg < 0, p);
      }
    } else if (pose === 'candle') {
      front += sleeve([-172, 500], [-30, 574], 84, 52, robeFill, p) + sleeve([172, 500], [30, 574], 84, 52, robeFill, p);
      front += candle(0, 446, 1, o.flame === undefined ? 1 : o.flame, o.t || 0, o.seed || 1);
      front += hand('fist', -20, 540, -75, 0.95, false, p) + hand('fist', 20, 540, 75, 0.95, true, p);
    }
    return { back, front };
  }

  function candle(x, y, sc, lit, t, seed) {
    let s = `<g transform="translate(${f(x)},${f(y)}) scale(${f(sc)})">`;
    s += `<rect x="-13" y="-10" width="26" height="120" rx="4" fill="#efe3c6" stroke="${OUT}" stroke-width="1.8"/>`;
    s += `<rect x="-13" y="-10" width="9" height="120" rx="3" fill="#ffffff" opacity="0.35"/>`;
    s += `<path d="M-13,-8 C-6,-4 6,-4 13,-8" fill="none" stroke="#cdbb92" stroke-width="2"/>`;
    s += `<path d="M0,-10 L0,-20" stroke="#2a1a10" stroke-width="2"/>`;
    if (lit > 0.02) {
      const fl = 1 + 0.08 * U.noise(t * 7, seed) ;
      const sway = 2.5 * U.noise(t * 3, seed + 4);
      s += `<g opacity="${f(lit)}">` +
        `<circle cx="0" cy="-34" r="${f(70 * fl)}" fill="url(#candleGlow)"/>` +
        `<path d="M0,-20 C-9,-28 -8,-42 ${f(sway)},${f(-60 * fl)} C8,-42 9,-28 0,-20Z" fill="#ffd27a"/>` +
        `<path d="M0,-21 C-4,-26 -4,-34 ${f(sway * 0.6)},${f(-44 * fl)} C4,-34 4,-26 0,-21Z" fill="#fff7d8"/>` +
        '</g>';
    }
    return s + '</g>';
  }

  // ---------------------------------------------------------------- main bust
  function bust(o) {
    const p = Object.assign({}, cast[o.who] || {}, o.pal || {});
    const id = o.id || o.who;
    const turn = o.turn || 0, tx = turn * 13;
    const side = o.lightSide || -1; // key light from the left by default
    const shadowSide = -side;
    const seed = o.seed || (id.length * 97 + 13);
    const open = clamp((o.open === undefined ? 1 : o.open) * (1 - (o.lid || 0) * 0.42) * (1 - (o.blink || 0)), 0, 1.2) * (o.lookY < 0 ? 1 - o.lookY * 0.12 : 1);
    const heavy = o.lid || 0;
    const lx = o.lookX || 0, ly = o.lookY || 0;
    const farL = turn > 0 ? 1 : 1 - Math.abs(turn) * 0.22;
    const farR = turn < 0 ? 1 : 1 - Math.abs(turn) * 0.22;
    const breathe = o.breathe || 0;
    const style = o.hairStyle || p.hairStyle, bstyle = o.beardStyle || p.beardStyle;
    const female = !!p.female;

    let s = defs(id, p, side);
    s += `<g transform="translate(${f(o.x)},${f(o.y)}) scale(${f(o.s || 1)}) rotate(${f(o.lean || 0)},0,700)">`;
    if (o.halo) {
      s += `<circle cx="0" cy="-10" r="190" fill="url(#haloGlow)"/>`;
      s += `<circle cx="0" cy="-10" r="168" fill="none" stroke="#f3cf6d" stroke-width="7" opacity="0.95"/>`;
      s += `<circle cx="0" cy="-10" r="158" fill="none" stroke="#fff1bf" stroke-width="2.5" opacity="0.8"/>`;
    }
    const A = arms(p, id, o);
    if (o.part === 'arms') return s + A.front + '</g>';
    s += A.back;
    // head group (tilted about the neck)
    const headT = `rotate(${f(o.tilt || 0)},0,110) translate(0,${f(-breathe * 2)})`;
    s += `<g transform="${headT}">${hairBack(style, p, id)}</g>`;
    // neck sits under the collar
    s += `<path d="M-35,82 C-37,120 -39,160 -46,200 L46,200 C39,160 37,120 35,82Z" fill="url(#${id}-neck)" stroke="${OUT}" stroke-width="1.6" stroke-opacity="0.7"/>`;
    s += `<g transform="translate(0,${f(-breathe * 1.2)}) scale(1,${f(1 + breathe * 0.004)})">${torso(p, id, o)}</g>`;
    const jaw = p.jaw || (female ? 'female' : p.child ? 'child' : p.young ? 'young' : 'male');
    s += `<g transform="${headT}">`;
    s += ear(-1, p, turn) + ear(1, p, turn);
    s += `<path d="${faceOutline(turn, jaw)}" fill="url(#${id}-skin)" stroke="${OUT}" stroke-width="2.2"/>`;
    // shading: shadow side of the face, eye sockets, cheek blush, forehead highlight
    s += `<ellipse cx="${f(shadowSide * 58 + tx * 0.5)}" cy="10" rx="34" ry="92" fill="url(#${id}-cheek)"/>`;
    s += `<ellipse cx="${f(-31 + tx)}" cy="-8" rx="26" ry="16" fill="url(#${id}-socket)"/>`;
    s += `<ellipse cx="${f(31 + tx)}" cy="-8" rx="26" ry="16" fill="url(#${id}-socket)"/>`;
    s += `<ellipse cx="${f(-side * -22 + tx)}" cy="-82" rx="46" ry="26" fill="url(#${id}-hi)"/>`;
    s += `<ellipse cx="${f(-38 + tx)}" cy="30" rx="20" ry="13" fill="url(#${id}-blush)"/>`;
    s += `<ellipse cx="${f(38 + tx)}" cy="30" rx="20" ry="13" fill="url(#${id}-blush)"/>`;
    if ((p.age || 0) > 0.35) {
      const a = p.age;
      s += `<path d="M-40,-62 C-20,-68 20,-68 40,-62 M-34,-50 C-14,-55 14,-55 34,-50" fill="none" stroke="${p.skinShade}" stroke-width="1.4" opacity="${f(a * 0.9)}"/>`;
      s += `<path d="M${f(-52 + tx)},6 l-7,-4 M${f(-52 + tx)},10 l-8,1 M${f(52 + tx)},6 l7,-4 M${f(52 + tx)},10 l8,1" stroke="${p.skinShade}" stroke-width="1.2" opacity="${f(a * 0.8)}"/>`;
      s += `<path d="M${f(-44 + tx)},14 C${f(-40 + tx)},18 ${f(-30 + tx)},20 ${f(-22 + tx)},16 M${f(44 + tx)},14 C${f(40 + tx)},18 ${f(30 + tx)},20 ${f(22 + tx)},16" fill="none" stroke="${p.skinShade}" stroke-width="1.2" opacity="${f(a * 0.6)}"/>`;
    }
    // features shift up a little when the head tilts back to look up
    s += `<g transform="translate(0,${f((o.pitch || 0) * 7)})">`;
    // eyes
    const eyeY = -2;
    s += eye(id, -33 + tx, eyeY, -1, farL * (female ? 1.04 : 1), open, lx, ly, p, heavy);
    s += eye(id, 33 + tx, eyeY, 1, farR * (female ? 1.04 : 1), open, lx, ly, p, heavy);
    if (female || p.young) {
      s += `<path d="M${f(-49 + tx)},${f(eyeY + 1)} l-4,-3 M${f(49 + tx)},${f(eyeY + 1)} l4,-3" stroke="${OUT}" stroke-width="1.8" stroke-linecap="round"/>`;
    }
    // brows
    const bR = o.browUp || 0, bS = o.browSad || 0;
    const browCol = p.brow || p.hairShade;
    s += brow(-32 + tx, -28, -1, bR, bS, browCol, farL);
    s += brow(32 + tx, -28, 1, bR, bS, browCol, farR);
    // nose
    s += nose(tx * 1.25, p, shadowSide, turn);
    // tears
    if (o.tear > 0) {
      const tx2 = (o.tearSide || -1) * 34 + tx;
      s += `<path d="M${f(tx2)},8 C${f(tx2 - 2)},20 ${f(tx2 + 1)},34 ${f(tx2 - 1)},${f(30 + 24 * o.tear)}" fill="none" stroke="#e8f4ff" stroke-width="3" opacity="${f(0.75 * o.tear)}" stroke-linecap="round"/>`;
      s += `<path d="M${f(-tx2 + 2 * tx)},8 C${f(-tx2 + 2 * tx + 2)},20 ${f(-tx2 + 2 * tx - 1)},30 ${f(-tx2 + 2 * tx + 1)},${f(26 + 14 * o.tear)}" fill="none" stroke="#e8f4ff" stroke-width="2.4" opacity="${f(0.5 * o.tear)}" stroke-linecap="round"/>`;
    }
    // beard + mouth
    const hasStache = bstyle === 'full' || bstyle === 'short' || bstyle === 'long' || bstyle === 'light';
    s += bstyle === 'light' ? `<g opacity="0.5">${beard('short', p, id, tx, turn, seed)}</g>` : beard(bstyle, p, id, tx, turn, seed);
    if (!hasStache && !female) {
      s += `<path d="M${f(-30 + tx)},62 C${f(-16 + tx)},58 ${f(16 + tx)},58 ${f(30 + tx)},62 L${f(26 + tx)},70 C${f(12 + tx)},66 ${f(-12 + tx)},66 ${f(-26 + tx)},70Z" fill="${p.beard}" opacity="${bstyle === 'stubble' ? 0.18 : 0}"/>`;
    }
    s += mouth(tx * 1.05, o.mouth || 0, o.smile || 0, p, hasStache);
    if (hasStache) s += `<g opacity="${bstyle === 'light' ? 0.55 : 1}">` + mustache(tx * 1.05, p, id, seed + 11, bstyle === 'short' || bstyle === 'light' ? 0.92 : 1) + '</g>';
    if (hasStache && bstyle !== 'light') s += `<path d="M${f(tx - 7)},${f(92 + (o.mouth || 0) * 9)} C${f(tx - 3)},${f(100 + (o.mouth || 0) * 9)} ${f(tx + 3)},${f(100 + (o.mouth || 0) * 9)} ${f(tx + 7)},${f(92 + (o.mouth || 0) * 9)}Z" fill="${shade(p.beard, -0.1)}"/>`;
    s += '</g>';
    s += hairFront(style, p, id, seed + 17, tx);
    s += '</g>';
    if (o.part !== 'body') s += A.front;
    if (o.rim) {
      // warm rim light on the key side of the silhouette
      s += `<path d="M${side * 150},220 C${side * 176},250 ${side * 184},300 ${side * 186},360" fill="none" stroke="${o.rim}" stroke-width="4" opacity="0.5" stroke-linecap="round"/>`;
    }
    s += '</g>';
    return s;
  }

  // ---------------------------------------------------------------- small full-body figures
  // Used in wide shots: walking disciples, Judas, people holding candles.
  // Walking figure in profile, facing +x (feet at y=0, ~300 units tall).
  function figureSide(o, p) {
    const ph = (o.phase || 0) * Math.PI * 2;
    const sw = Math.sin(ph), bob = Math.abs(Math.cos(ph)) * 3;
    const robe = p.robe, robeShade = p.robeShade, mantle = p.mantle;
    const style = o.hairStyle || p.hairStyle;
    let s = `<g transform="translate(${f(o.x)},${f(o.y)}) scale(${f(o.s || 1)})">`;
    if (o.shadow !== false) s += `<ellipse cx="0" cy="2" rx="46" ry="8" fill="#000" opacity="0.3"/>`;
    // feet (sandals) under the hem
    const fa = 16 * sw, fb = -16 * sw;
    s += `<path d="M${f(fa - 10)},-2 C${f(fa - 10)},-10 ${f(fa + 12)},-10 ${f(fa + 20)},-3 L${f(fa + 20)},1 L${f(fa - 10)},1Z" fill="#3a2414"/>`;
    s += `<path d="M${f(fb - 10)},-2 C${f(fb - 10)},-10 ${f(fb + 12)},-10 ${f(fb + 20)},-3 L${f(fb + 20)},1 L${f(fb - 10)},1Z" fill="#2a1a0e"/>`;
    s += `<g transform="translate(0,${f(-bob)})">`;
    // back arm
    const arm = 22 * sw;
    s += `<path d="M-4,-238 C-8,-210 ${f(-6 - arm * 0.5)},-180 ${f(-4 - arm)},-150 L${f(8 - arm)},-148 C${f(10 - arm * 0.5)},-176 12,-206 12,-232Z" fill="${shade(robe, -0.25)}" stroke="${OUT}" stroke-width="2"/>`;
    // robe: narrow at the shoulders, wider at the hem, hem swings with the stride
    const h1 = -36 + sw * 8, h2 = 42 + sw * 8;
    s += `<path d="M-20,-246 C-30,-230 -32,-180 -32,-140 C-32,-90 ${f(h1 - 2)},-50 ${f(h1)},-10 L${f(h2)},-10 C${f(h2 + 2)},-50 36,-100 32,-150 C30,-190 28,-230 20,-246Z" fill="${robe}" stroke="${OUT}" stroke-width="2.2"/>`;
    s += `<path d="M-6,-200 C-8,-140 ${f(h1 + 18)},-70 ${f(h1 + 22)},-12 M14,-196 C18,-130 ${f(h2 - 16)},-60 ${f(h2 - 18)},-12" fill="none" stroke="${robeShade}" stroke-width="2.4" opacity="0.8"/>`;
    if (mantle) {
      s += `<path d="M-24,-240 C-6,-252 18,-250 26,-236 C30,-200 22,-150 6,-110 C-10,-120 -26,-150 -34,-180 C-36,-205 -32,-228 -24,-240Z" fill="${mantle}" stroke="${OUT}" stroke-width="2"/>`;
      if (p.trim) s += `<path d="M26,-236 C30,-200 22,-150 6,-110" fill="none" stroke="${p.trim}" stroke-width="3.5"/>`;
    }
    // near arm, swinging opposite to the back arm
    s += `<path d="M-2,-238 C4,-210 ${f(8 + arm * 0.5)},-182 ${f(10 + arm)},-152 L${f(-2 + arm)},-148 C${f(-4 + arm * 0.5)},-176 -10,-206 -12,-232Z" fill="${shade(robe, 0.05)}" stroke="${OUT}" stroke-width="2"/>`;
    s += `<circle cx="${f(5 + arm)}" cy="-146" r="7.5" fill="${p.skin}" stroke="${OUT}" stroke-width="1.6"/>`;
    if (o.lantern) {
      const lx = 10 + arm, ly = -140;
      s += `<path d="M${f(lx)},${f(ly)} l0,10" stroke="#2a1a10" stroke-width="2"/>` +
        `<rect x="${f(lx - 8)}" y="${f(ly + 10)}" width="16" height="22" rx="3" fill="#ffd27a" stroke="#4a3018" stroke-width="2"/>`;
    }
    // neck + head in profile
    s += `<path d="M-4,-262 L10,-262 L12,-244 L-6,-244Z" fill="${p.skinShade}"/>`;
    s += `<g transform="translate(4,-282)">`;
    if (style === 'long') s += `<path d="M-20,-12 C-30,6 -30,30 -24,48 L-8,46 C-12,30 -10,10 -4,0Z" fill="${p.hair}" stroke="${OUT}" stroke-width="1.6"/>`;
    s += `<path d="M-2,-24 C10,-26 18,-18 18,-10 L24,0 L19,4 L20,9 L17,15 C14,20 6,22 -2,21 C-12,20 -22,12 -22,-2 C-22,-16 -14,-24 -2,-24Z" fill="${p.skin}" stroke="${OUT}" stroke-width="1.8" stroke-linejoin="round"/>`;
    if (p.beardStyle === 'full' || p.beardStyle === 'short' || p.beardStyle === 'light') {
      s += `<path d="M-6,4 C-2,10 6,10 12,8 L19,9 L17,16 C14,24 4,28 -4,24 C-10,20 -12,12 -6,4Z" fill="${p.beard}" opacity="${p.beardStyle === 'light' ? 0.5 : 1}"/>`;
    }
    s += `<path d="M8,-7 C10,-9 14,-9 15,-7" fill="none" stroke="${OUT}" stroke-width="1.8" stroke-linecap="round"/>`;
    if (style === 'headcloth' || style === 'veil' || o.hood) {
      const c = o.hood || (style === 'veil' ? p.veil : p.cloth);
      s += `<path d="M-26,24 C-30,0 -26,-26 -4,-30 C10,-32 18,-26 20,-16 L12,-14 C4,-18 -10,-14 -12,0 C-12,14 -10,26 -6,40 L-30,44Z" fill="${c}" stroke="${OUT}" stroke-width="1.8"/>`;
      if (p.band) s += `<path d="M-14,-22 C-4,-26 8,-24 14,-18" fill="none" stroke="${p.band}" stroke-width="4"/>`;
    } else {
      s += `<path d="M-24,4 C-28,-18 -14,-30 2,-28 C12,-27 18,-22 18,-14 C10,-18 2,-18 -4,-12 C-8,-6 -8,2 -10,10 C-16,12 -22,10 -24,4Z" fill="${p.hair}" stroke="${OUT}" stroke-width="1.6"/>`;
      s += `<path d="M-12,2 C-14,-2 -12,-6 -8,-6" fill="none" stroke="${p.skinShade}" stroke-width="2"/>`;
    }
    s += '</g></g></g>';
    return s;
  }

  function figure(o) {
    const p = Object.assign({}, cast[o.who] || {}, o.pal || {});
    if (o.view === 'side') return figureSide(o, p);
    const ph = o.phase || 0;
    const view = o.view || 'back';
    const sw = Math.sin(ph * Math.PI * 2);
    const bob = Math.abs(Math.cos(ph * Math.PI * 2)) * 3;
    const robe = o.robe || p.robe, robeShade = o.robeShade || p.robeShade;
    const mantle = o.mantle !== undefined ? o.mantle : p.mantle;
    let s = `<g transform="translate(${f(o.x)},${f(o.y)}) scale(${f((o.s || 1) * (o.flip ? -1 : 1))},${f(o.s || 1)})">`;
    if (o.shadow !== false) s += `<ellipse cx="0" cy="2" rx="48" ry="9" fill="#000" opacity="0.25"/>`;
    s += `<g transform="translate(0,${f(-bob)})">`;
    // feet
    if (view === 'side') {
      s += `<path d="M${f(-6 + sw * 16)},-6 l22,0 l2,6 l-26,0Z M${f(-6 - sw * 16)},-6 l22,0 l2,6 l-26,0Z" fill="#3a2516"/>`;
    } else {
      s += `<path d="M${f(-18 + sw * 3)},${f(-4 - Math.max(0, sw) * 6)} l14,0 l0,6 l-16,0Z M${f(6 - sw * 3)},${f(-4 - Math.max(0, -sw) * 6)} l14,0 l0,6 l-16,0Z" fill="#3a2516"/>`;
    }
    // robe (A-line), hem sways with the stride
    const hem = sw * 6;
    s += `<path d="M-30,-232 C-44,-226 -50,-200 -50,-170 C-52,-110 -56,-50 ${f(-52 + hem)},-6 L${f(52 + hem)},-6 C56,-50 52,-110 50,-170 C50,-200 44,-226 30,-232Z" fill="${robe}" stroke="${OUT}" stroke-width="2.2"/>`;
    s += `<path d="M-20,-200 C-24,-140 ${f(-30 + hem)},-70 ${f(-28 + hem)},-8 M16,-196 C22,-140 ${f(24 + hem)},-70 ${f(26 + hem)},-8" fill="none" stroke="${robeShade}" stroke-width="2.4" opacity="0.8"/>`;
    if (mantle) {
      s += `<path d="M-34,-230 C-10,-236 30,-232 44,-214 C54,-180 52,-120 46,-70 C20,-90 -10,-120 -40,-150 C-48,-180 -46,-212 -34,-230Z" fill="${mantle}" stroke="${OUT}" stroke-width="2"/>`;
      if (p.trim) s += `<path d="M-40,-150 C-10,-120 20,-90 46,-70" fill="none" stroke="${p.trim}" stroke-width="3"/>`;
    }
    if (o.belt) s += `<path d="M-48,-150 C-20,-144 20,-144 48,-150 L48,-142 C20,-136 -20,-136 -48,-142Z" fill="${o.belt}"/>`;
    // arms
    const armSw = o.carry ? 0 : sw * 10;
    s += `<path d="M-40,-222 C-56,-200 ${f(-58 + armSw * 0.3)},-160 ${f(-52 + armSw)},-118 L${f(-38 + armSw)},-116 C-40,-150 -36,-190 -28,-214Z" fill="${shade(robe, -0.06)}" stroke="${OUT}" stroke-width="2"/>`;
    s += `<path d="M40,-222 C56,-200 ${f(58 - armSw * 0.3)},-160 ${f(52 - armSw)},-118 L${f(38 - armSw)},-116 C40,-150 36,-190 28,-214Z" fill="${shade(robe, -0.06)}" stroke="${OUT}" stroke-width="2"/>`;
    if (view !== 'back') {
      s += `<circle cx="${f(-45 + armSw)}" cy="-112" r="7" fill="${p.skin}" stroke="${OUT}" stroke-width="1.5"/>`;
      s += `<circle cx="${f(45 - armSw)}" cy="-112" r="7" fill="${p.skin}" stroke="${OUT}" stroke-width="1.5"/>`;
    }
    if (o.lantern) {
      const lx = 52 - armSw, ly = -100;
      s += `<circle cx="${f(lx)}" cy="${f(ly + 12)}" r="60" fill="url(#lanternGlow)"/>` +
        `<path d="M${f(lx)},${f(ly - 6)} l0,8" stroke="#2a1a10" stroke-width="2"/>` +
        `<rect x="${f(lx - 7)}" y="${f(ly + 2)}" width="14" height="20" rx="3" fill="#ffcf73" stroke="#4a3018" stroke-width="2"/>`;
    }
    if (o.bag) s += `<path d="M${f(46 - armSw)},-118 c-8,6 -10,22 0,26 c10,4 18,-6 14,-18 c-2,-6 -8,-10 -14,-8Z" fill="#6a4a2a" stroke="${OUT}" stroke-width="1.6"/>`;
    // head
    const style = o.hairStyle || p.hairStyle;
    s += `<g transform="translate(0,-262)">`;
    if (view === 'back') {
      if (style === 'headcloth' || style === 'veil' || o.hood) {
        const c = o.hood || (style === 'veil' ? p.veil : p.cloth);
        s += `<path d="M-30,-6 C-34,-32 -14,-44 0,-44 C14,-44 34,-32 30,-6 C32,10 36,26 40,36 L-40,36 C-36,26 -32,10 -30,-6Z" fill="${c}" stroke="${OUT}" stroke-width="2"/>`;
      } else {
        const long = style === 'long';
        s += `<path d="M-26,-4 C-30,-30 -14,-42 0,-42 C14,-42 30,-30 26,-4 C${long ? '30,20 34,36 30,48 L-30,48 C-34,36 -30,20 -26,-4' : '24,14 14,24 0,24 C-14,24 -24,14 -26,-4'}Z" fill="${p.hair}" stroke="${OUT}" stroke-width="2"/>`;
        s += `<path d="M-10,-36 C-14,-10 -12,10 -16,30 M8,-36 C12,-10 10,10 14,30" fill="none" stroke="${p.hairShade}" stroke-width="1.6" opacity="0.7"/>`;
      }
    } else {
      // front or side: simple face
      const fx = view === 'side' ? 6 : 0;
      s += `<path d="M${-22 + fx},-6 C${-24 + fx},-30 ${-10 + fx},-40 ${2 + fx},-40 C${16 + fx},-40 ${26 + fx},-28 ${24 + fx},-6 C${22 + fx},12 ${12 + fx},22 ${1 + fx},22 C${-10 + fx},22 ${-20 + fx},12 ${-22 + fx},-6Z" fill="${p.skin}" stroke="${OUT}" stroke-width="2"/>`;
      if (p.beardStyle === 'full' || p.beardStyle === 'short') {
        s += `<path d="M${-21 + fx},-2 C${-20 + fx},14 ${-8 + fx},26 ${2 + fx},28 C${12 + fx},26 ${22 + fx},14 ${23 + fx},-2 C${16 + fx},6 ${10 + fx},8 ${2 + fx},8 C${-6 + fx},8 ${-14 + fx},6 ${-21 + fx},-2Z" fill="${p.beard}"/>`;
      }
      s += `<circle cx="${-7 + fx * 1.6}" cy="-10" r="2.2" fill="#1a0e08"/><circle cx="${9 + fx * 1.6}" cy="-10" r="2.2" fill="#1a0e08"/>`;
      if (style === 'long') s += `<path d="M${2 + fx},-44 C-26,-44 -30,-20 -28,10 C-28,30 -32,44 -30,50 L-18,48 C-20,30 -20,0 -16,-20 C-10,-34 20,-34 22,-20 C26,0 24,30 22,48 L34,50 C32,40 30,24 30,6 C32,-24 28,-44 2,-44Z" fill="${p.hair}" stroke="${OUT}" stroke-width="1.8"/>`;
      else if (style === 'headcloth' || style === 'veil') s += `<path d="M-30,10 C-34,-30 -14,-48 2,-48 C18,-48 36,-30 32,10 L26,40 L20,0 C18,-24 -14,-26 -18,0 L-24,40Z" fill="${style === 'veil' ? p.veil : p.cloth}" stroke="${OUT}" stroke-width="1.8"/>`;
      else s += `<path d="M-23,-8 C-26,-34 -12,-44 2,-44 C16,-44 28,-34 25,-8 C20,-24 10,-28 2,-28 C-8,-28 -18,-24 -23,-8Z" fill="${p.hair}" stroke="${OUT}" stroke-width="1.8"/>`;
    }
    s += '</g></g></g>';
    return s;
  }

  window.RIG = { bust, figure, cast, candle, bread, hand };
})();
