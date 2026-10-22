// Procedural unit sprites, drawn like painted tabletop miniatures.
// Every sprite faces right in local units (1 unit = 1/48 of a tile's width) with its
// feet at (0, 0); the caller flips the context for left-facing units.
(function (root) {
  'use strict';
  const AG = (root.AG = root.AG || {});

  const OUT = '#17121b';
  const TEAMS = {
    P: { main: '#3f7fd9', light: '#93c0ff', dark: '#1e4688', ring: '#5ea2ff', glow: 'rgba(94,162,255,' },
    E: { main: '#c93c36', light: '#ff9888', dark: '#741c1a', ring: '#ff5d52', glow: 'rgba(255,93,82,' },
  };

  // ------------------------------------------------------------ helpers

  function hex(c) {
    const n = parseInt(c.slice(1), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function shade(c, amt) {
    const [r, g, b] = hex(c);
    const f = (v) => Math.max(0, Math.min(255, Math.round(amt >= 0 ? v + (255 - v) * amt : v * (1 + amt))));
    return 'rgb(' + f(r) + ',' + f(g) + ',' + f(b) + ')';
  }

  function finish(ctx, fill, lw) {
    if (fill) {
      ctx.fillStyle = fill;
      ctx.fill();
    }
    if (lw !== 0) {
      ctx.lineWidth = lw || 1.2;
      ctx.strokeStyle = OUT;
      ctx.lineJoin = 'round';
      ctx.stroke();
    }
  }
  function rect(ctx, x, y, w, h, r, fill, lw) {
    ctx.beginPath();
    if (r && ctx.roundRect) ctx.roundRect(x, y, w, h, r);
    else ctx.rect(x, y, w, h);
    finish(ctx, fill, lw);
  }
  function circle(ctx, x, y, r, fill, lw) {
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    finish(ctx, fill, lw);
  }
  function ellipse(ctx, x, y, rx, ry, fill, lw, rot) {
    ctx.beginPath();
    ctx.ellipse(x, y, rx, ry, rot || 0, 0, Math.PI * 2);
    finish(ctx, fill, lw);
  }
  function poly(ctx, pts, fill, lw) {
    ctx.beginPath();
    ctx.moveTo(pts[0], pts[1]);
    for (let i = 2; i < pts.length; i += 2) ctx.lineTo(pts[i], pts[i + 1]);
    ctx.closePath();
    finish(ctx, fill, lw);
  }
  function line(ctx, x1, y1, x2, y2, w, color, outline) {
    ctx.lineCap = 'round';
    if (outline !== false) {
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.lineWidth = w + 2.2;
      ctx.strokeStyle = OUT;
      ctx.stroke();
    }
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.lineWidth = w;
    ctx.strokeStyle = color;
    ctx.stroke();
  }
  function glow(ctx, x, y, r, color, alpha) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, color + alpha + ')');
    g.addColorStop(1, color + '0)');
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }

  // ------------------------------------------------------------ body parts

  function legs(ctx, c, boot) {
    rect(ctx, -5, -12, 4.2, 11, 1.2, c);
    rect(ctx, 0.8, -12, 4.2, 11, 1.2, shade(c, -0.12));
    rect(ctx, -5.6, -3.2, 5, 3.4, 1.2, boot || shade(c, -0.45));
    rect(ctx, 0.6, -3.2, 5.8, 3.4, 1.2, boot || shade(c, -0.45));
  }

  function torso(ctx, c, top, w) {
    w = w || 7;
    rect(ctx, -w, top, w * 2, -top - 10, 3, c);
    ctx.fillStyle = 'rgba(255,255,255,0.13)';
    ctx.fillRect(-w + 1.5, top + 1.5, w - 1, 3);
  }

  function face(ctx, x, y, r, skin, back) {
    circle(ctx, x, y, r, skin);
    if (!back) {
      ctx.fillStyle = OUT;
      ctx.fillRect(x + r * 0.35, y - r * 0.2, 1.3, 1.6);
      ctx.fillStyle = 'rgba(180,80,60,0.35)';
      ctx.fillRect(x + r * 0.1, y + r * 0.35, 2.2, 1);
    }
  }

  function arm(ctx, x1, y1, x2, y2, c, hand) {
    line(ctx, x1, y1, x2, y2, 3.6, c);
    circle(ctx, x2, y2, 1.9, hand || '#e2b48c', 1);
  }

  function cape(ctx, c, top, len) {
    poly(ctx, [-6, top, 6, top, 9, top + len, -9, top + len], shade(c, -0.15));
    ctx.fillStyle = 'rgba(255,255,255,0.1)';
    ctx.fillRect(-1, top + 2, 2, len - 4);
  }

  const SKIN = '#e5b892';

  // ------------------------------------------------------------ units

  const D = {};

  D.knight = (ctx, o) => {
    const T = o.tc;
    const back = o.back;
    if (back) {
      // Shield slung over the shoulder, sword at the right.
      legs(ctx, '#8d96a5');
      torso(ctx, '#aeb7c4', -25);
      cape(ctx, T.main, -24, 20);
      poly(ctx, [-12, -26, -3, -26, -3, -14, -7.5, -8, -12, -14], shade(T.main, -0.2));
      arm(ctx, 6, -22, 10, -14, '#aeb7c4', '#9aa3b0');
      line(ctx, 10, -14, 15, -33, 2.6, '#dfe6ee');
      line(ctx, 8, -17, 12.5, -15.5, 2, '#d8b04a');
      rect(ctx, -5.5, -36, 11, 12, 3, '#b3bcc9');
      poly(ctx, [-1, -36, 2, -42 + o.bob, 7, -40, 4, -35], T.main);
      return;
    }
    legs(ctx, '#8d96a5');
    torso(ctx, '#b9c2cf', -25);
    rect(ctx, -4.5, -24, 9, 13, 1.5, T.main);
    line(ctx, 0, -22, 0, -14, 1.4, T.light, false);
    line(ctx, -2.5, -19.5, 2.5, -19.5, 1.4, T.light, false);
    circle(ctx, -6.5, -23, 3.2, '#c5cdd8');
    circle(ctx, 6.5, -23, 3.2, '#c5cdd8');
    arm(ctx, 6.5, -22, 10, -14, '#b9c2cf', '#9aa3b0');
    // sword
    line(ctx, 10, -14, 15.5, -35, 2.6, '#e8eef5');
    line(ctx, 7.8, -17, 12.6, -15.4, 2.2, '#d8b04a');
    // helm and plume
    rect(ctx, -5.5, -36, 11, 12, 3, '#c3cbd6');
    rect(ctx, 0.5, -31.5, 5, 1.6, 0.6, OUT, 0);
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.fillRect(-4, -34.5, 3, 4);
    poly(ctx, [-1, -36, 2, -42 + o.bob, 7, -40, 4, -35], T.main);
    if (o.lord) poly(ctx, [-5.5, -35, -5.5, -39, -3, -37, 0, -40, 3, -37, 5.5, -39, 5.5, -35], '#e6b83c', 0.8);
    // kite shield on the off arm
    poly(ctx, [-13, -25, -3, -25, -3, -13, -8, -6, -13, -13], T.main);
    poly(ctx, [-11.2, -23.3, -4.8, -23.3, -4.8, -13.8, -8, -9.2, -11.2, -13.8], T.dark, 0);
    line(ctx, -8, -22, -8, -11, 1.6, T.light, false);
    line(ctx, -10.5, -18.5, -5.5, -18.5, 1.6, T.light, false);
  };

  D.archer = (ctx, o) => {
    const T = o.tc;
    const back = o.back;
    legs(ctx, '#6b4a2e');
    if (back) {
      torso(ctx, '#4d7438', -24);
      rect(ctx, -5, -27, 6, 15, 2, '#7a5530');
      line(ctx, -3.5, -27, -3.5, -31, 1.4, '#e8e0cc', false);
      line(ctx, -1.5, -27, -0.5, -31.5, 1.4, '#e8e0cc', false);
      circle(ctx, 0.5, -29, 6, '#3f6330');
      arm(ctx, 6, -21, 10, -16, '#4d7438', SKIN);
      ctx.beginPath();
      ctx.arc(9, -22, 12, -1.15, 1.15);
      ctx.lineWidth = 3.2;
      ctx.strokeStyle = OUT;
      ctx.stroke();
      ctx.lineWidth = 1.8;
      ctx.strokeStyle = '#8a5a2b';
      ctx.stroke();
      return;
    }
    rect(ctx, -6, -28, 5, 14, 2, '#7a5530');
    torso(ctx, '#557f3e', -24);
    line(ctx, -6, -23, 6, -13, 2, T.main, false);
    rect(ctx, -7, -13.5, 14, 2.4, 0.8, '#5a3d22', 0);
    poly(ctx, [-6, -31, 0, -38, 7, -31, 6, -24, -6, -24], '#47702f');
    face(ctx, 1, -29, 4.6, SKIN);
    arm(ctx, -5, -21, -8, -14, '#557f3e', SKIN);
    arm(ctx, 5, -21, 9.5, -21, '#557f3e', SKIN);
    // bow
    ctx.beginPath();
    ctx.arc(7.5, -21, 13, -1.05, 1.05);
    ctx.lineWidth = 3.4;
    ctx.strokeStyle = OUT;
    ctx.stroke();
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#94612e';
    ctx.stroke();
    line(ctx, 14, -32, 14, -10, 0.7, '#efe8d8', false);
    line(ctx, 3, -21, 17.5, -21, 1, '#d9cfb8', false);
    poly(ctx, [17.5, -22.6, 20.5, -21, 17.5, -19.4], '#cfd6de', 0.8);
  };

  D.scout = (ctx, o) => {
    const T = o.tc;
    ctx.save();
    ctx.scale(0.92, 0.92);
    legs(ctx, '#7b5634');
    torso(ctx, '#a6763f', -23, 6);
    rect(ctx, -6, -14, 12, 2.2, 0.8, '#4f3520', 0);
    for (let i = 0; i < 3; i++) line(ctx, -4 + i * 3, -14, -4.5 + i * 3, -11, 1, '#c7cdd4', false);
    if (o.back) {
      circle(ctx, 0.5, -28, 5, '#5a3c22');
      poly(ctx, [-4, -31, 5, -31, 5, -28, -4, -28], T.main);
      line(ctx, -4, -29.5, -9, -26 + o.bob, 1.8, T.main);
      arm(ctx, 5, -20, 9, -14, '#a6763f', SKIN);
      line(ctx, 9, -14, 12, -20, 1.8, '#dfe5ec');
      ctx.restore();
      return;
    }
    face(ctx, 0.8, -28, 4.8, SKIN);
    poly(ctx, [-5, -31.5, 5.5, -31.5, 5.5, -28.6, -5, -28.6], T.main);
    line(ctx, -5, -30, -10, -27 + o.bob, 1.8, T.main);
    arm(ctx, -5, -20, -7.5, -13, '#a6763f', SKIN);
    arm(ctx, 5, -20, 10, -17, '#a6763f', SKIN);
    line(ctx, 10, -17, 15, -22, 1.8, '#e3e9f0');
    ctx.restore();
  };

  D.cleric = (ctx, o) => {
    const T = o.tc;
    // robe
    poly(ctx, [-7, -25, 7, -25, 10, 0, -10, 0], '#ece4d2');
    poly(ctx, [-10, 0, 10, 0, 9.3, -3, -9.3, -3], '#d6b24c', 0);
    if (o.back) {
      poly(ctx, [-7, -25, 7, -25, 9, -6, -9, -6], '#ddd3bd');
      circle(ctx, 0.5, -29.5, 5.6, '#e3dac6');
      arm(ctx, 6, -22, 10, -15, '#ece4d2', SKIN);
      line(ctx, 10, -4, 12, -38, 1.8, '#7a5634');
      circle(ctx, 12.2, -39, 3, '#e8c65a');
      return;
    }
    rect(ctx, -4.5, -25, 2.6, 22, 1, T.main, 0);
    rect(ctx, 1.9, -25, 2.6, 22, 1, T.main, 0);
    line(ctx, -7, -12, 7, -12, 1.4, '#d6b24c', false);
    poly(ctx, [-6.5, -29, 0, -36, 7, -29, 6.5, -24, -6.5, -24], '#e9e0cb');
    face(ctx, 1.2, -29, 4.4, SKIN);
    line(ctx, -3, -32.8, 5, -32.8, 1.3, '#e3c25a', false);
    arm(ctx, -5.5, -21, -8, -14, '#ece4d2', SKIN);
    arm(ctx, 5.5, -21, 10, -16, '#ece4d2', SKIN);
    line(ctx, 11, -2, 12.5, -39, 1.8, '#7a5634');
    // sun disc
    const pulse = 0.5 + 0.5 * Math.sin(o.t * 3);
    glow(ctx, 12.7, -40, 7 + pulse * 2, 'rgba(255,220,120,', 0.45);
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      line(ctx, 12.7, -40, 12.7 + Math.cos(a) * 5, -40 + Math.sin(a) * 5, 0.9, '#f3d36a', false);
    }
    circle(ctx, 12.7, -40, 2.8, '#f6d86d', 1);
  };

  D.berserker = (ctx, o) => {
    const T = o.tc;
    rect(ctx, -6, -12, 4.6, 12, 1.2, '#5a3a24');
    rect(ctx, 1.4, -12, 4.6, 12, 1.2, '#4d321f');
    poly(ctx, [-8, -15, 8, -15, 9, -8, -9, -8], '#7a5532');
    for (let i = -7; i <= 7; i += 3.5) poly(ctx, [i - 1.6, -8.5, i + 1.6, -8.5, i, -6], '#a77d4f', 0);
    if (o.back) {
      rect(ctx, -8, -27, 16, 13, 4, '#cf9a71');
      circle(ctx, 0.5, -31, 6.2, '#c4542a');
      line(ctx, -6, -24, 6, -17, 2, T.main, false);
      line(ctx, -3, -10, 12, -40, 2.4, '#6b4a2b');
      poly(ctx, [10, -42, 17, -40, 18, -33, 12, -36], '#cdd4dc');
      return;
    }
    rect(ctx, -8, -27, 16, 13, 4, '#dca47a');
    line(ctx, -3, -22, 3, -22, 0.8, 'rgba(120,60,40,0.5)', false);
    rect(ctx, -9, -24, 3, 3, 1, T.main, 0.8);
    face(ctx, 1, -31, 5.2, '#dca47a');
    poly(ctx, [-5.8, -32, -3, -38, 0, -35, 3, -39, 6, -34, 6.5, -31, -5.5, -29], '#c4542a');
    poly(ctx, [-1, -28, 6, -28, 4.5, -23, -0.5, -24], '#b84c25');
    line(ctx, 1.5, -32, 6, -32, 1.2, T.main, false);
    arm(ctx, -7, -24, -9, -15, '#dca47a', '#dca47a');
    arm(ctx, 7, -24, 9, -16, '#dca47a', '#dca47a');
    // great axe
    line(ctx, -2, -8, 12, -40, 2.4, '#6b4a2b');
    poly(ctx, [10.5, -43, 18.5, -41, 19.5, -32, 13, -35], '#d3dae2');
    poly(ctx, [10.5, -43, 5, -44, 4, -37, 10, -38], '#bcc4cd');
  };

  D.pyromancer = (ctx, o) => {
    const T = o.tc;
    poly(ctx, [-7, -25, 7, -25, 10.5, 0, -10.5, 0], '#a83d25');
    poly(ctx, [-10.5, 0, 10.5, 0, 9.8, -3, -9.8, -3], '#5e1e12', 0);
    const flick = Math.sin(o.t * 9) * 0.8 + Math.sin(o.t * 13) * 0.5;
    if (o.back) {
      poly(ctx, [-7, -25, 7, -25, 9.5, -5, -9.5, -5], '#93351f');
      poly(ctx, [-6.5, -27, 0, -41, 7, -27], '#7c2b18');
      arm(ctx, 6, -22, 10, -15, '#a83d25', SKIN);
      line(ctx, 10, -3, 12, -35, 1.8, '#3e2a1c');
      glow(ctx, 12.3, -38, 9, 'rgba(255,140,40,', 0.55);
      circle(ctx, 12.3, -38 + flick * 0.3, 3, '#ffb347', 1);
      return;
    }
    rect(ctx, -2, -25, 4, 23, 1, T.main, 0);
    poly(ctx, [-6.5, -27, 0, -42, 7.5, -27, 6, -23, -6, -23], '#8a2f1b');
    circle(ctx, 1.4, -27.5, 4, '#3a1a12', 0);
    circle(ctx, 3.2, -28, 0.9, '#ffb347', 0);
    arm(ctx, -5.5, -21, -8, -14, '#a83d25', SKIN);
    arm(ctx, 5.5, -21, 10, -16, '#a83d25', SKIN);
    line(ctx, 11, -2, 12.5, -35, 1.8, '#3e2a1c');
    glow(ctx, 12.8, -38, 10 + flick, 'rgba(255,140,40,', 0.6);
    poly(ctx, [10, -37, 12.8, -45 - flick, 15.6, -37, 12.8, -34], '#ff8a2a', 0.9);
    circle(ctx, 12.8, -38, 2, '#ffe08a', 0);
  };

  D.assassin = (ctx, o) => {
    const T = o.tc;
    // crouched, low silhouette
    rect(ctx, -6, -10, 4.4, 10, 1.2, '#2a2230');
    rect(ctx, 1.6, -9, 4.4, 9, 1.2, '#241d2a');
    poly(ctx, [-7, -22, 7, -24, 8, -10, -7, -10], '#352b40');
    line(ctx, -6, -21, -13, -18 + o.bob * 1.5, 2.4, T.main);
    if (o.back) {
      poly(ctx, [-6, -26, 0, -33, 7, -26, 6, -20, -6, -20], '#2b2333');
      arm(ctx, 6, -20, 10, -14, '#352b40', '#3d3346');
      line(ctx, 10, -14, 14, -18, 1.6, '#dfe5ec');
      return;
    }
    poly(ctx, [-6, -26, 0.5, -34, 7.5, -26, 6.5, -20, -6, -20], '#2b2333');
    rect(ctx, 0, -28.5, 6, 3, 1, '#d8c7b4', 0);
    ctx.fillStyle = '#f2e27a';
    ctx.fillRect(3, -27.8, 1.4, 1.2);
    arm(ctx, -5, -20, -9, -15, '#352b40', '#3d3346');
    line(ctx, -9, -15, -12, -11, 1.6, '#dfe5ec');
    arm(ctx, 5.5, -20, 11, -18, '#352b40', '#3d3346');
    line(ctx, 11, -18, 17, -21, 1.8, '#e8eef5');
  };

  D.golem = (ctx, o) => {
    const T = o.tc;
    const stone = o.king ? '#6f675b' : '#8e877a';
    const dark = o.king ? '#544d43' : '#6c665b';
    rect(ctx, -9, -12, 7, 12, 2, dark);
    rect(ctx, 2, -12, 7, 12, 2, shade(dark, -0.08));
    poly(ctx, [-12, -34, 11, -36, 13, -14, -12, -12], stone);
    poly(ctx, [-12, -34, 11, -36, 9, -30, -10, -29], shade(stone, 0.15), 0);
    if (o.king) {
      for (const [a, b, c, d] of [[-6, -30, -2, -22], [4, -32, 7, -24], [-3, -18, 3, -15]]) line(ctx, a, b, c, d, 1.2, '#ffa040', false);
    }
    ellipse(ctx, -8, -20, 2.5, 1.5, '#5d7a3c', 0);
    if (!o.back) {
      circle(ctx, 0, -23, 3.2, T.dark, 0.8);
      glow(ctx, 0, -23, 6, T.glow, 0.5);
      circle(ctx, 0, -23, 1.6, T.light, 0);
    }
    // head
    rect(ctx, -4, -42, 10, 8, 2, stone);
    if (!o.back) {
      ctx.fillStyle = T.light;
      ctx.fillRect(1, -39.5, 1.8, 1.8);
      ctx.fillRect(4, -39.5, 1.8, 1.8);
      glow(ctx, 3.5, -38.5, 5, T.glow, 0.45);
    }
    if (o.king) {
      poly(ctx, [-4, -42, -4, -47, -1.5, -44, 1, -48, 3.5, -44, 6, -47, 6, -42], '#e6b83c');
    }
    // boulder fists
    const sway = o.bob * 0.6;
    line(ctx, -11, -31, -15, -16, 5, stone);
    circle(ctx, -15, -14 + sway, 4.5, dark);
    line(ctx, 11, -32, 15, -17, 5, stone);
    circle(ctx, 15.5, -15 - sway, 4.8, dark);
  };

  D.beastrider = (ctx, o) => {
    const T = o.tc;
    const fur = '#6e6a66';
    const step = Math.sin(o.t * 4) * 0.8;
    // wolf in profile, facing right
    poly(ctx, [-16, -18, -20, -23 + o.bob, -17, -16], fur);
    rect(ctx, -13, -9, 3.4, 9, 1, shade(fur, -0.2));
    rect(ctx, 8, -9, 3.4, 9, 1, shade(fur, -0.2));
    ellipse(ctx, -1, -14, 15, 6.5, fur);
    rect(ctx, -10, -9, 3.4, 9 + step, 1, fur);
    rect(ctx, 5, -9, 3.4, 9 - step, 1, fur);
    poly(ctx, [10, -20, 18, -22, 24, -17, 22, -14, 14, -12, 9, -14], fur);
    poly(ctx, [12, -21, 13.5, -26, 15.5, -21], shade(fur, -0.15));
    ctx.fillStyle = '#f0d36a';
    ctx.fillRect(18, -19.5, 1.6, 1.4);
    rect(ctx, -8, -21, 12, 5, 1.5, T.main);
    // rider
    rect(ctx, -4, -33, 9, 13, 3, '#8b6440');
    if (o.back) {
      cape(ctx, T.main, -32, 11);
      circle(ctx, 0.5, -36, 4.6, '#9aa3b0');
    } else {
      face(ctx, 1.5, -36, 4.2, SKIN);
      poly(ctx, [-3, -37.5, 6, -37.5, 5, -41.5, -2, -41.5], '#9aa3b0');
    }
    arm(ctx, 3, -30, 8, -26, '#8b6440', SKIN);
    line(ctx, -6, -23, 22, -40, 1.8, '#a07a4c');
    poly(ctx, [22, -40, 26.5, -43, 23.5, -38.5], '#dfe5ec', 0.8);
    poly(ctx, [16, -36.5, 20.5, -39.2, 19, -34], T.main, 0.8);
  };

  D.furgon = (ctx, o) => {
    const T = o.tc;
    const bark = '#6e5133';
    poly(ctx, [-9, 0, -6, -3, -10, -1], bark);
    poly(ctx, [9, 0, 6, -3, 10, -1], bark);
    poly(ctx, [-7, -2, 7, -2, 6, -26, -6, -26], bark);
    line(ctx, -3, -6, -2, -22, 0.8, 'rgba(0,0,0,0.3)', false);
    line(ctx, 3, -5, 2.5, -20, 0.8, 'rgba(0,0,0,0.3)', false);
    line(ctx, -6, -18, -13, -24 + o.bob, 2, bark);
    line(ctx, 6, -18, 13, -22 - o.bob, 2, bark);
    for (const [x, y, r, c] of [
      [-6, -30, 7, '#3f7a30'],
      [5, -31, 7, '#3f7a30'],
      [0, -36, 8, '#4c8f3a'],
      [-3, -28, 6, '#5aa046'],
      [4, -27, 5.5, '#4c8f3a'],
    ])
      circle(ctx, x, y, r, c);
    circle(ctx, 2, -38, 2.4, T.main, 0.8);
    if (!o.back) {
      ctx.fillStyle = '#d8f06a';
      ctx.fillRect(0.5, -17, 1.8, 1.8);
      ctx.fillRect(4, -17, 1.8, 1.8);
      glow(ctx, 3, -16, 5, 'rgba(216,240,106,', 0.35);
    }
  };

  D.wisp = (ctx, o) => {
    const y = -20 + o.bob * 2.2;
    const f = Math.sin(o.t * 7);
    glow(ctx, 0, y, 17, 'rgba(140,230,90,', 0.45);
    poly(ctx, [-7, y, -4, y + 13 + f, -1, y + 6, 2, y + 15 - f, 5, y + 5, 7, y], '#3f8f2a', 1);
    poly(ctx, [-7, y + 1, -5, y - 12 - f * 1.5, -1, y - 7, 2, y - 15 + f, 4, y - 8, 7, y - 11 - f, 8, y + 1], '#5fb83a', 1);
    circle(ctx, 0, y, 7, '#a8f06a', 1.2);
    circle(ctx, -1.5, y - 2, 3, '#e4ffc0', 0);
    if (!o.back) {
      ctx.fillStyle = OUT;
      ctx.fillRect(1, y - 1, 1.6, 2.4);
      ctx.fillRect(4, y - 1, 1.6, 2.4);
    }
  };

  D.barrier = (ctx, o) => {
    const T = o.tc;
    poly(ctx, [-9, 0, 9, 0, 6, -12, -6, -12], '#7a7684');
    rect(ctx, -6.5, -9, 13, 3, 0.8, T.main, 0.8);
    poly(ctx, [-6, -12, 6, -12, 4, -15, -4, -15], '#8f8b99');
    const y = -27 + o.bob * 1.5;
    glow(ctx, 0, y, 16, 'rgba(120,220,255,', 0.4);
    poly(ctx, [0, y - 11, 6, y, 0, y + 9, -6, y], '#86e1ff', 1.2);
    poly(ctx, [0, y - 11, 2.5, y, 0, y + 9, -1.5, y], '#d7f7ff', 0);
    ctx.globalAlpha = 0.25 + 0.1 * Math.sin(o.t * 2);
    ellipse(ctx, 0, -18, 15, 19, null, 0);
    ctx.strokeStyle = '#a8ecff';
    ctx.lineWidth = 0.8;
    ctx.stroke();
    ctx.globalAlpha = 1;
  };

  D.enchantress = (ctx, o) => {
    const T = o.tc;
    poly(ctx, [-6, -24, 6, -24, 11, 0, -11, 0], '#b8408d');
    poly(ctx, [-11, 0, 11, 0, 10.3, -3, -10.3, -3], '#f08bd0', 0);
    if (o.back) {
      rect(ctx, -6, -24, 12, 10, 3, '#a8387f', 0);
      circle(ctx, 0.5, -29.5, 5.2, '#e3b34e');
      poly(ctx, [-5, -28, 5.8, -28, 4.5, -15, 0.5, -12.5, -4, -15], '#e3b34e');
      line(ctx, 0.5, -26, 0.5, -15, 0.8, 'rgba(120,80,20,0.4)', false);
      arm(ctx, 5.5, -21, 10, -18, '#b8408d', SKIN);
      line(ctx, 10, -18, 13, -25, 1.4, '#f0e2c0');
      return;
    }
    rect(ctx, -2, -24, 4, 4, 1, T.main, 0.8);
    poly(ctx, [-6.5, -33, 4, -35, 7, -26, 6, -18, -7.5, -16], '#e3b34e');
    face(ctx, 1.6, -29, 4.4, SKIN);
    arm(ctx, -5, -21, -8, -14, '#b8408d', SKIN);
    arm(ctx, 5, -21, 11, -22, '#b8408d', SKIN);
    line(ctx, 11, -22, 15, -30, 1.4, '#f0e2c0');
    const tw = 0.5 + 0.5 * Math.sin(o.t * 5);
    glow(ctx, 15.5, -31, 7 + tw * 2, 'rgba(255,140,220,', 0.5);
    poly(ctx, [15.5, -35, 16.6, -32, 19.5, -31, 16.6, -30, 15.5, -27, 14.4, -30, 11.5, -31, 14.4, -32], '#ffd2f2', 0.8);
  };

  D.witch = (ctx, o) => {
    const T = o.tc;
    const s = o.queen ? 1 : 1;
    poly(ctx, [-7, -24, 7, -24, 11, 0, 6, -2, 3, 0, -1, -2, -5, 0, -11, 0], '#3b2450');
    if (o.queen) cape(ctx, T.main, -24, 22);
    if (o.back) {
      poly(ctx, [-6, -32, 6, -32, 7, -18, -7, -18], '#1f1626');
      ellipse(ctx, 0, -32, 11, 2.6, '#2a1d38');
      poly(ctx, [-6, -33, 6, -33, 2, -46, -3, -43], '#2a1d38');
      rect(ctx, -6, -35, 12, 2, 0.6, T.main, 0);
      arm(ctx, 6, -21, 10, -16, '#3b2450', '#e6dcd2');
      return;
    }
    rect(ctx, -2, -24, 4, 22, 1, shade(T.main, -0.2), 0);
    poly(ctx, [-6, -32, 6, -32, 7, -18, -7, -18], '#1f1626');
    face(ctx, 1.4, -29, 4.4, '#e6dcd2');
    ellipse(ctx, 0, -32.5, 11.5, 2.8, '#2a1d38');
    poly(ctx, [-6, -33, 6, -33, 4, -42, 9, -47, 0, -44, -3, -43], '#2a1d38');
    rect(ctx, -6, -35.5, 12, 2.2, 0.6, T.main, 0);
    if (o.queen) poly(ctx, [-4, -36, -4, -40, -2, -38, 0, -41, 2, -38, 4, -40, 4, -36], '#e6b83c', 0.8);
    arm(ctx, -5.5, -21, -8, -14, '#3b2450', '#e6dcd2');
    arm(ctx, 5.5, -21, 10, -18, '#3b2450', '#e6dcd2');
    line(ctx, 10, -18, 14, -33, 1.6, '#2b2030');
    const c = 0.5 + 0.5 * Math.sin(o.t * 6);
    glow(ctx, 14.3, -34, 7 + c * 2, 'rgba(170,90,255,', 0.55);
    poly(ctx, [14.3, -38, 16.5, -34, 14.3, -30, 12.1, -34], '#b06cff', 0.9);
    void s;
  };

  D.lightning = (ctx, o) => {
    const T = o.tc;
    poly(ctx, [-8, 0, 8, 0, 6, -24, -6, -24], '#6d6458');
    rect(ctx, -6.2, -16, 12.4, 3, 0.8, T.main, 0.8);
    if (!o.back) {
      ctx.fillStyle = OUT;
      ctx.fillRect(-3, -21, 2, 2);
      ctx.fillRect(1.5, -21, 2, 2);
      rect(ctx, -2.5, -9, 5, 1.6, 0.6, OUT, 0);
    }
    poly(ctx, [-6, -24, 6, -24, 3, -28, -3, -28], '#857a6c');
    const y = -34;
    glow(ctx, 0, y, 14, 'rgba(255,220,80,', 0.5);
    poly(ctx, [0, y - 8, 5, y, 0, y + 6, -5, y], '#ffd84a', 1.2);
    poly(ctx, [0, y - 8, 2, y, 0, y + 6, -1, y], '#fff3b0', 0);
    if (Math.sin(o.t * 11) > 0.3) {
      line(ctx, 3, y - 3, 8, y - 7, 0.9, '#fff3b0', false);
      line(ctx, 8, y - 7, 7, y - 10, 0.9, '#fff3b0', false);
    }
    if (Math.sin(o.t * 7 + 1) > 0.4) line(ctx, -3, y + 1, -8, y - 2, 0.9, '#fff3b0', false);
  };

  D.dragon = (ctx, o) => {
    const T = o.tc;
    const ash = o.tyrant;
    const drake = o.drake;
    const body = ash ? '#3d3633' : drake ? '#c0602e' : '#8e2f24';
    const belly = ash ? '#7a5a44' : drake ? '#f0c060' : '#e3a24c';
    const wing = ash ? '#2a2422' : drake ? '#8a3a1c' : '#6d2119';
    const memb = ash ? '#5a2f20' : drake ? '#d97a3a' : '#a8432f';
    const flap = Math.sin(o.t * 3) * 3;
    // far wing
    poly(ctx, [-4, -26, -16, -48 - flap, -24, -40 - flap, -22, -28, -12, -24], wing);
    poly(ctx, [-6, -27, -16, -45 - flap, -21, -38 - flap, -19, -29], memb, 0);
    // tail
    poly(ctx, [-12, -14, -26, -10, -32, -16, -28, -8, -12, -8], body);
    // legs
    rect(ctx, -9, -10, 5, 10, 1.5, shade(body, -0.2));
    rect(ctx, 5, -10, 5, 10, 1.5, shade(body, -0.2));
    // body
    ellipse(ctx, -1, -16, 15, 9, body);
    ellipse(ctx, 1, -13, 10, 5, belly, 0);
    rect(ctx, -7, -8, 5, 8, 1.5, body);
    rect(ctx, 7, -8, 5, 8, 1.5, body);
    // neck and head
    poly(ctx, [6, -20, 12, -34, 18, -34, 13, -18], body);
    poly(ctx, [11, -36, 24, -34, 27, -30, 17, -29, 12, -30], body);
    poly(ctx, [17, -29, 26, -29, 22, -26, 17, -27], shade(body, -0.25));
    poly(ctx, [12, -36, 9, -43, 14, -37], '#e8dcc0');
    poly(ctx, [15, -36, 14, -42, 18, -36], '#e8dcc0');
    if (!o.back) {
      ctx.fillStyle = ash ? '#ff7a2a' : '#ffd84a';
      ctx.fillRect(18.5, -33.5, 2, 1.6);
    }
    if (ash) {
      for (const [a, b, c, d] of [[-8, -20, -3, -14], [2, -22, 6, -15], [8, -28, 12, -24]]) line(ctx, a, b, c, d, 1, '#ff7a2a', false);
      glow(ctx, 0, -16, 16, 'rgba(255,120,40,', 0.2);
    }
    // near wing
    poly(ctx, [0, -24, 8, -50 + flap, 0, -44 + flap, -8, -46 + flap, -10, -28], wing);
    poly(ctx, [-1, -26, 6, -47 + flap, 0, -42 + flap, -7, -43 + flap, -8, -29], memb, 0);
    line(ctx, -4, -18, -4, -12, 2.2, T.main, false);
    rect(ctx, -6, -21, 7, 3, 1, T.main, 0.8);
  };

  D.shrub = (ctx, o) => {
    const T = o.tc;
    for (const [x, y, r, c] of [
      [-6, -6, 6, '#2f6a2a'],
      [6, -6, 6, '#2f6a2a'],
      [0, -11, 7.5, '#3d7f33'],
      [-3, -6, 5.5, '#4a9440'],
      [4, -9, 4.5, '#56a24a'],
    ])
      circle(ctx, x, y, r, c);
    for (const [x, y] of [[-9, -10], [8, -12], [-2, -18], [3, -4]]) line(ctx, x, y, x + 2, y - 2, 0.9, '#d9e6b0', false);
    circle(ctx, -3, -12, 1.3, T.main, 0.6);
    circle(ctx, 5, -5, 1.3, T.main, 0.6);
  };

  D.specter = (ctx, o) => {
    const T = o.tc;
    const y = -5 + o.bob * 1.6;
    const f = Math.sin(o.t * 4);
    const a = ctx.globalAlpha;
    ctx.globalAlpha = a * 0.88;
    glow(ctx, 0, y - 18, 17, 'rgba(170,215,255,', 0.35);
    poly(ctx, [-8, y - 25, 8, y - 25, 11, y - 6, 8, y - 1 + f, 5, y - 5, 1, y + f, -3, y - 5, -7, y - 1 - f, -11, y - 6], '#b8d3e6');
    poly(ctx, [-5, y - 20, 5, y - 20, 6, y - 8, -6, y - 8], '#d5e7f3', 0);
    line(ctx, 6, y - 20, 12, y - 14 - f, 2, '#b8d3e6');
    line(ctx, -6, y - 20, -11, y - 13 + f, 2, '#b8d3e6');
    poly(ctx, [-7.5, y - 24, 0.5, y - 38, 8, y - 24, 6.5, y - 19, -6.5, y - 19], '#9dbcd3');
    ellipse(ctx, 1.5, y - 26, 3.8, 4.2, '#15202b', 0);
    if (!o.back) {
      ctx.fillStyle = T.light;
      ctx.fillRect(1.2, y - 27, 1.4, 1.4);
      ctx.fillRect(3.6, y - 27, 1.4, 1.4);
    }
    ctx.globalAlpha = a;
  };

  D.warbanner = (ctx, o) => {
    const T = o.tc;
    const w = Math.sin(o.t * 3);
    poly(ctx, [-8, 0, 8, 0, 6, -5, -6, -5], '#6f6a66');
    line(ctx, 0, -5, 0, -56, 2.4, '#5a3d22');
    line(ctx, -1, -54, 13, -54, 1.6, '#5a3d22');
    poly(ctx, [0, -53, 15, -53 + w * 0.6, 15, -29 + w, 7.5, -34 + w * 0.8, 0, -29], T.main);
    poly(ctx, [0, -53, 15, -53 + w * 0.6, 15, -50 + w * 0.6, 0, -50], T.dark, 0);
    circle(ctx, 7, -42 + w * 0.5, 3.2, T.light, 0.8);
    line(ctx, 7, -45 + w * 0.5, 7, -39 + w * 0.5, 1, T.dark, false);
    poly(ctx, [-1.6, -57, 1.6, -57, 0, -62], '#e6b83c', 0.8);
  };

  D.cage = (ctx, o) => {
    const T = o.tc;
    poly(ctx, [-13, 0, 13, 0, 12, -4, -12, -4], '#5a4128');
    circle(ctx, -4, -16, 3, '#d9b38f', 0.8);
    rect(ctx, -7, -13, 6, 9, 2, '#7a6a55', 0.8);
    circle(ctx, 4.5, -15 + o.bob * 0.4, 3, '#c9a07a', 0.8);
    rect(ctx, 1.5, -12, 6, 8, 2, '#6a5a48', 0.8);
    for (let x = -11; x <= 11.5; x += 4.4) line(ctx, x, -4, x, -27, 1.4, '#3d3a3e');
    rect(ctx, -12, -17, 24, 1.6, 0.6, '#3d3a3e', 0);
    poly(ctx, [-14, -27, 14, -27, 11, -31, -11, -31], '#4a4548');
    rect(ctx, -2, -12, 4, 4, 1, T.main, 0.8);
  };

  // ------------------------------------------------------------ v2 heroes

  D.mageknight = (ctx, o) => {
    const T = o.tc;
    const steel = '#7e88a6';
    const pulse = 0.5 + 0.5 * Math.sin(o.t * 4);
    legs(ctx, '#5f6884');
    if (o.back) {
      torso(ctx, steel, -25);
      cape(ctx, T.main, -24, 19);
      arm(ctx, 6, -22, 10, -14, steel, '#9aa3b0');
      line(ctx, 10, -14, 15, -34, 2.6, '#d9ccff');
      rect(ctx, -5.5, -36, 11, 12, 3, '#8c96b3');
      poly(ctx, [-5, -34, -9, -41, -3.5, -36], '#c9a94a', 0.8);
      poly(ctx, [5, -34, 9, -41, 3.5, -36], '#c9a94a', 0.8);
      return;
    }
    torso(ctx, steel, -25);
    rect(ctx, -4.5, -24, 9, 12, 1.5, T.main);
    glow(ctx, 0, -19, 6, 'rgba(180,140,255,', 0.3 + 0.3 * pulse);
    line(ctx, -2, -21.5, 2, -16.5, 1.1, '#efe6ff', false);
    line(ctx, 2, -21.5, -2, -16.5, 1.1, '#efe6ff', false);
    circle(ctx, -6.5, -23, 3.2, '#98a2bf');
    circle(ctx, 6.5, -23, 3.2, '#98a2bf');
    arm(ctx, -6, -21, -9, -14, steel, '#9aa3b0');
    arm(ctx, 6.5, -22, 10, -14, steel, '#9aa3b0');
    glow(ctx, 13, -25, 9, 'rgba(180,140,255,', 0.2 + 0.2 * pulse);
    line(ctx, 10, -14, 15.5, -35, 2.8, '#ddd2ff');
    line(ctx, 11.6, -19, 14.6, -31, 0.9, '#8f6cff', false);
    line(ctx, 7.8, -17, 12.6, -15.4, 2.2, '#c9a94a');
    rect(ctx, -5.5, -36, 11, 12, 3, '#9aa4c2');
    rect(ctx, 0.5, -31.5, 5, 1.6, 0.6, '#2a1f45', 0);
    ctx.fillStyle = 'rgba(210,190,255,' + (0.6 + 0.4 * pulse) + ')';
    ctx.fillRect(2, -31.2, 2.6, 1);
    poly(ctx, [-5, -34, -9, -41, -3.5, -36], '#c9a94a', 0.8);
    poly(ctx, [5, -34, 9, -41, 3.5, -36], '#c9a94a', 0.8);
  };

  // Bare bones: legs, pelvis, spine and ribs.
  function skeletonBody(ctx, o) {
    const bone = '#e6dfc9';
    const dark = '#b9b19a';
    line(ctx, -3, -12, -4, -1.5, 1.8, bone);
    line(ctx, 3, -12, 3.5, -1.5, 1.8, dark);
    rect(ctx, -6.5, -2.2, 4.5, 2.2, 0.8, dark, 0.8);
    rect(ctx, 1.8, -2.2, 5, 2.2, 0.8, dark, 0.8);
    poly(ctx, [-5, -14.5, 5, -14.5, 4, -11, -4, -11], dark);
    line(ctx, 0, -14, 0, -27, 1.8, dark);
    for (let i = 0; i < 3; i++) line(ctx, -5 + i * 0.6, -25 + i * 2.8, 5 - i * 0.6, -25 + i * 2.8, 1.2, bone);
    line(ctx, -5.5, -25.5, 5.5, -15, 1.6, o.tc.main, false);
  }

  function skull(ctx, x, y, r, back, eye) {
    circle(ctx, x, y, r, '#e9e3cd');
    if (back) return;
    rect(ctx, x - r * 0.1, y + r * 0.45, r * 1.05, r * 0.55, 0.6, '#d8d0b8', 0.8);
    ctx.fillStyle = OUT;
    ctx.beginPath();
    ctx.arc(x + r * 0.35, y - r * 0.05, r * 0.28, 0, Math.PI * 2);
    ctx.arc(x + r * 0.85, y - r * 0.05, r * 0.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = eye || '#9fe0ff';
    ctx.fillRect(x + r * 0.28, y - r * 0.12, 1, 1);
  }

  D.skelarcher = (ctx, o) => {
    skeletonBody(ctx, o);
    skull(ctx, 1, -31, 5, o.back);
    if (o.back) {
      rect(ctx, -5, -27, 5, 13, 2, '#5d4630');
      arm(ctx, 4, -23, 9, -18, '#e6dfc9', '#e6dfc9');
      ctx.beginPath();
      ctx.arc(8, -22, 11, -1.15, 1.15);
      ctx.lineWidth = 3;
      ctx.strokeStyle = OUT;
      ctx.stroke();
      ctx.lineWidth = 1.7;
      ctx.strokeStyle = '#a69a7a';
      ctx.stroke();
      return;
    }
    arm(ctx, -4, -23, -7, -16, '#e6dfc9', '#e6dfc9');
    arm(ctx, 4, -23, 9, -22, '#e6dfc9', '#e6dfc9');
    ctx.beginPath();
    ctx.arc(7, -22, 12, -1.05, 1.05);
    ctx.lineWidth = 3.2;
    ctx.strokeStyle = OUT;
    ctx.stroke();
    ctx.lineWidth = 1.9;
    ctx.strokeStyle = '#b3a684';
    ctx.stroke();
    line(ctx, 13, -32.5, 13, -11.5, 0.7, '#d8d2c0', false);
    line(ctx, 3, -22, 16.5, -22, 1, '#d9cfb8', false);
    poly(ctx, [16.5, -23.5, 19.5, -22, 16.5, -20.5], '#cfe9f5', 0.8);
  };

  // ------------------------------------------------------------ greenskins

  const ORC = '#6f9a4a';
  const GOB = '#8db14a';

  function tusks(ctx, x, y) {
    poly(ctx, [x, y, x + 1, y - 3, x + 2, y], '#f2ecd8', 0.6);
  }

  D.orc = (ctx, o) => {
    const T = o.tc;
    const skin = o.skin || ORC;
    legs(ctx, '#5a4632', '#3a2a1c');
    if (o.back) {
      rect(ctx, -8, -27, 16, 15, 4, '#6b5a44');
      line(ctx, -7, -24, 7, -16, 2, T.main, false);
      circle(ctx, 0.5, -31, 5.8, skin);
      poly(ctx, [-2, -36, 3, -36, 1, -41], '#2f2418');
      arm(ctx, 7, -24, 10, -15, skin, skin);
      line(ctx, 10, -15, 14, -30, 2, '#5a3d22');
      poly(ctx, [12, -33, 18, -31, 17, -26, 13, -28], '#a9b1b9');
      return;
    }
    rect(ctx, -8, -27, 16, 15, 4, '#7d6c54');
    ctx.fillStyle = 'rgba(30,25,20,0.35)';
    for (let i = 0; i < 4; i++) for (let j = 0; j < 3; j++) ctx.fillRect(-6 + i * 3.4, -25 + j * 3.2, 1.4, 1.4);
    rect(ctx, -8.5, -15.5, 17, 3, 1, '#4a3a28', 0);
    rect(ctx, -2, -15.8, 4, 3.4, 0.8, T.main, 0.8);
    circle(ctx, -7.5, -25, 3.4, '#5d4a35');
    face(ctx, 1.5, -31.5, 5.8, skin);
    line(ctx, -0.5, -34, 5.5, -33, 1.4, '#3d5a26', false);
    tusks(ctx, 3, -28.4);
    tusks(ctx, 5.4, -28.4);
    poly(ctx, [-3, -36.5, 2, -37.5, 0, -41], '#2f2418');
    arm(ctx, -7, -24, -9, -15, skin, skin);
    arm(ctx, 7, -24, 10, -17, skin, skin);
    line(ctx, 10, -17, 12, -33, 2.2, '#5a3d22');
    poly(ctx, [10.5, -36, 18.5, -33.5, 17, -26, 11.5, -28], '#aeb6be');
    line(ctx, 12, -34.5, 17.5, -32.5, 0.9, '#e8edf2', false);
  };

  D.brute = (ctx, o) => {
    const T = o.tc;
    const skin = '#5f8a3e';
    rect(ctx, -8, -12, 6, 12, 1.5, '#4d3b29');
    rect(ctx, 2, -12, 6, 12, 1.5, '#44331f');
    rect(ctx, -9, -2.5, 7, 3, 1, '#2d2016', 0.9);
    rect(ctx, 1.5, -2.5, 8, 3, 1, '#2d2016', 0.9);
    if (o.back) {
      rect(ctx, -11, -31, 22, 20, 6, skin);
      rect(ctx, -10, -30, 20, 8, 3, '#5b4a37', 0.8);
      line(ctx, -9, -27, 9, -14, 2.2, T.main, false);
      circle(ctx, 0.5, -34, 5.6, skin);
      arm(ctx, 10, -27, 13, -15, skin, skin);
      line(ctx, 13, -15, 16, -38, 2.6, '#5a3d22');
      rect(ctx, 11, -45, 11, 8, 2, '#7d858c');
      return;
    }
    rect(ctx, -11, -31, 22, 20, 6, skin);
    rect(ctx, -9, -24, 18, 9, 2, '#6b5a44', 0.9);
    rect(ctx, -10, -15, 20, 3.4, 1, '#3e2e1f', 0);
    rect(ctx, -2.2, -15.4, 4.4, 4, 0.8, T.main, 0.8);
    circle(ctx, -9.5, -28.5, 4.6, '#7d858c');
    circle(ctx, 9.5, -28.5, 4.6, '#7d858c');
    face(ctx, 2, -34.5, 5.6, skin);
    line(ctx, -0.5, -37, 6.5, -36, 1.6, '#3d5a26', false);
    tusks(ctx, 3.4, -31.4);
    tusks(ctx, 5.8, -31.4);
    arm(ctx, -10, -27, -13, -16, skin, skin);
    arm(ctx, 10, -27, 13, -17, skin, skin);
    line(ctx, 13, -15, 16, -38, 2.6, '#5a3d22');
    rect(ctx, 11, -46, 11, 9, 2, '#80888f');
    rect(ctx, 11, -43, 11, 2, 0.5, '#5b6268', 0);
  };

  D.goblin_archer = (ctx, o) => {
    const T = o.tc;
    ctx.save();
    ctx.scale(0.82, 0.82);
    legs(ctx, '#5f4a2f', '#3a2a1c');
    poly(ctx, [-6, -24, 6, -24, 8, -11, -8, -11], '#6a5236');
    line(ctx, -6, -23, 6, -13, 1.8, T.main, false);
    if (o.back) {
      poly(ctx, [-6, -26, 0, -36, 6.5, -26, 6, -21, -6, -21], '#4f3d27');
      poly(ctx, [-6, -30, -13, -33, -6, -27], GOB);
      arm(ctx, 5, -21, 9, -16, GOB, GOB);
      ctx.restore();
      return;
    }
    face(ctx, 1.5, -28.5, 5, GOB);
    poly(ctx, [-3, -29, -12, -33, -4, -26], GOB);
    poly(ctx, [5, -31, 12, -35, 6, -28], GOB);
    poly(ctx, [-6, -30, 0, -38, 7, -30, 6, -27, -6, -27], '#4f3d27');
    ctx.fillStyle = '#ffde59';
    ctx.fillRect(3, -29.5, 1.6, 1.3);
    arm(ctx, -5, -21, -8, -14, GOB, GOB);
    arm(ctx, 5, -21, 9.5, -21, GOB, GOB);
    ctx.beginPath();
    ctx.arc(7.5, -21, 10, -1.05, 1.05);
    ctx.lineWidth = 3;
    ctx.strokeStyle = OUT;
    ctx.stroke();
    ctx.lineWidth = 1.8;
    ctx.strokeStyle = '#7a5530';
    ctx.stroke();
    line(ctx, 12.5, -29.5, 12.5, -12.5, 0.6, '#efe8d8', false);
    line(ctx, 3, -21, 15, -21, 0.9, '#d9cfb8', false);
    ctx.restore();
  };

  D.sapper = (ctx, o) => {
    const T = o.tc;
    ctx.save();
    ctx.scale(0.82, 0.82);
    const spark = 0.5 + 0.5 * Math.sin(o.t * 18);
    legs(ctx, '#5f4a2f', '#3a2a1c');
    // the keg on its back
    rect(ctx, -14, -28, 10, 13, 3, '#7a4f28');
    rect(ctx, -14.5, -25, 11, 1.6, 0.4, '#3e3a36', 0);
    rect(ctx, -14.5, -19, 11, 1.6, 0.4, '#3e3a36', 0);
    line(ctx, -9, -28, -7, -33, 1, '#3a2a1c', false);
    glow(ctx, -7, -33.5, 4 + spark * 2, 'rgba(255,190,80,', 0.8);
    circle(ctx, -7, -33.5, 1.2, '#fff1a8', 0);
    poly(ctx, [-6, -24, 6, -24, 8, -11, -8, -11], '#7b5e3a');
    line(ctx, -6, -23, 6, -13, 1.8, T.main, false);
    if (o.back) {
      circle(ctx, 0.5, -29, 4.8, GOB);
      ctx.restore();
      return;
    }
    face(ctx, 1.5, -28.5, 5, GOB);
    poly(ctx, [-3, -29, -11, -33, -4, -26], GOB);
    poly(ctx, [5, -31, 12, -35, 6, -28], GOB);
    rect(ctx, -3.5, -33.5, 9, 3, 1, '#5b4a37', 0.8);
    ctx.fillStyle = '#ffde59';
    ctx.fillRect(3, -29.5, 1.6, 1.3);
    poly(ctx, [1, -26, 6, -26, 4, -24.5], '#f2ecd8', 0.5);
    arm(ctx, 5, -21, 9.5, -19, GOB, GOB);
    circle(ctx, 10.5, -19, 2.4, '#3e3a36');
    ctx.restore();
  };

  D.shaman = (ctx, o) => {
    const T = o.tc;
    const skin = ORC;
    poly(ctx, [-7, -25, 7, -25, 10, 0, -10, 0], '#5c4632');
    poly(ctx, [-10, 0, 10, 0, 9.4, -3, -9.4, -3], T.main, 0);
    for (let i = -7; i <= 7; i += 3.5) poly(ctx, [i - 1.4, -25, i + 1.4, -25, i, -21], '#e8dfc4', 0.6);
    if (o.back) {
      circle(ctx, 0.5, -30, 5.6, skin);
      poly(ctx, [-6, -31, -9, -40, -3, -34], '#d9cfb8', 0.8);
      poly(ctx, [6, -31, 9, -40, 3, -34], '#d9cfb8', 0.8);
      arm(ctx, 6, -22, 10, -15, skin, skin);
      line(ctx, 10, -3, 12, -38, 1.8, '#5a3d22');
      return;
    }
    face(ctx, 1.5, -30, 5.6, skin);
    tusks(ctx, 3.2, -26.6);
    // bone mask and horns
    poly(ctx, [-1, -34, 7, -34, 7, -29.5, -1, -29.5], '#e8dfc4', 0.8);
    ctx.fillStyle = OUT;
    ctx.fillRect(1.5, -32.6, 1.6, 1.4);
    ctx.fillRect(4.6, -32.6, 1.6, 1.4);
    poly(ctx, [-5, -33, -9, -42, -2, -35], '#d9cfb8', 0.8);
    poly(ctx, [6, -34, 9, -43, 4, -35], '#d9cfb8', 0.8);
    // war drum at the hip
    const beat = Math.max(0, Math.sin(o.t * 6)) * 1.5;
    ellipse(ctx, -8, -13, 5, 6, '#8a5a30');
    ellipse(ctx, -8, -13, 3.5, 4.4, '#e8d7b0', 0.8);
    arm(ctx, -5, -22, -7, -15 - beat, skin, skin);
    arm(ctx, 5.5, -22, 10, -17, skin, skin);
    line(ctx, 11, -3, 12.5, -39, 1.8, '#5a3d22');
    for (const [dx, c] of [[-2, '#c4542a'], [2, '#3f7fd9']]) line(ctx, 12.5, -36, 12.5 + dx, -30, 1, c, false);
    circle(ctx, 12.6, -39.5, 2.4, '#e8dfc4');
  };

  // ------------------------------------------------------------ beasts

  function wolfBody(ctx, o, fur, big) {
    const k = big ? 1.15 : 1;
    const step = Math.sin(o.t * 5) * 0.9;
    ctx.save();
    ctx.scale(k, k);
    poly(ctx, [-14, -14, -20, -19 + o.bob, -16, -12], fur);
    rect(ctx, -11, -8, 3.2, 8, 1, shade(fur, -0.25));
    rect(ctx, 6, -8, 3.2, 8, 1, shade(fur, -0.25));
    ellipse(ctx, -1, -12, 13, 5.8, fur);
    ellipse(ctx, 0, -9.5, 9, 3, shade(fur, 0.15), 0);
    rect(ctx, -8, -8, 3.2, 8 + step, 1, fur);
    rect(ctx, 3, -8, 3.2, 8 - step, 1, fur);
    poly(ctx, [8, -17, 16, -19, 22, -14, 20, -11, 12, -10, 7, -12], fur);
    poly(ctx, [10, -18, 11.5, -23, 13.5, -18], shade(fur, -0.2));
    poly(ctx, [13, -18.5, 15, -23, 16, -18], shade(fur, -0.2));
    if (!o.back) {
      ctx.fillStyle = big ? '#ff5a3a' : '#f0d36a';
      ctx.fillRect(16, -16.5, 1.7, 1.3);
      poly(ctx, [19, -11.5, 21, -11.5, 20, -9.5], '#f2ecd8', 0.5);
    }
    rect(ctx, -6, -18, 8, 2.4, 1, o.tc.main, 0.8);
    ctx.restore();
  }

  D.warg = (ctx, o) => wolfBody(ctx, o, '#4e4a46', true);
  D.wolf = (ctx, o) => wolfBody(ctx, o, '#8d8a85', false);

  D.spider = (ctx, o) => {
    const T = o.tc;
    const body = '#3b3340';
    const sc = Math.sin(o.t * 6);
    for (let i = 0; i < 4; i++) {
      const lx = -10 + i * 6;
      const lift = (i % 2 ? sc : -sc) * 1.2;
      line(ctx, lx, -9, lx - 5, -15 + lift, 1.6, shade(body, -0.2));
      line(ctx, lx - 5, -15 + lift, lx - 7, 0, 1.6, shade(body, -0.2));
    }
    ellipse(ctx, -6, -11, 9, 7.5, body);
    ellipse(ctx, -6, -12, 5, 3.5, T.main, 0.8);
    poly(ctx, [-8, -14, -4, -14, -6, -9], '#d94a3a', 0);
    ellipse(ctx, 6, -8, 6, 5, shade(body, 0.1));
    for (let i = 0; i < 4; i++) {
      const lx = -8 + i * 6;
      const lift = (i % 2 ? -sc : sc) * 1.2;
      line(ctx, lx, -7, lx + 6, -13 + lift, 1.8, body);
      line(ctx, lx + 6, -13 + lift, lx + 8, 0, 1.8, body);
    }
    if (!o.back) {
      ctx.fillStyle = '#ff5a3a';
      for (const [x, y] of [[9, -10], [10.6, -9], [9.5, -8], [11, -7.5]]) ctx.fillRect(x, y, 1.2, 1.2);
      line(ctx, 11, -5.5, 12.5, -3, 1, '#d8d0b8', false);
    }
  };

  D.troll = (ctx, o) => {
    const T = o.tc;
    const skin = '#7b8f6a';
    const moss = '#55703f';
    rect(ctx, -9, -12, 6.5, 12, 2, shade(skin, -0.15));
    rect(ctx, 2.5, -12, 6.5, 12, 2, shade(skin, -0.22));
    poly(ctx, [-10, -14, 10, -14, 11, -8, -11, -8], '#5a4632');
    if (o.back) {
      ellipse(ctx, 0, -26, 12, 13, skin);
      for (const [x, y, r] of [[-5, -32, 3], [3, -30, 3.4], [-1, -24, 2.6]]) circle(ctx, x, y, r, moss, 0);
      circle(ctx, 3, -38, 5, skin);
      arm(ctx, 10, -27, 13, -12, skin, skin);
      line(ctx, 13, -12, 16, -30, 3.4, '#6b4a2b');
      return;
    }
    ellipse(ctx, 0, -26, 12, 13, skin);
    ellipse(ctx, 2, -22, 7, 7, shade(skin, 0.12), 0);
    for (const [x, y, r] of [[-7, -31, 3], [-9, -24, 2.4]]) circle(ctx, x, y, r, moss, 0);
    rect(ctx, -6, -15, 12, 3, 1, T.main, 0.8);
    face(ctx, 6, -36, 5, skin);
    poly(ctx, [8.5, -35, 13, -33, 9, -32], shade(skin, -0.1));
    tusks(ctx, 7, -32.6);
    line(ctx, 3, -39, 9, -38.5, 1.4, '#3d4d30', false);
    arm(ctx, -10, -28, -13, -12, skin, skin);
    arm(ctx, 10, -28, 13, -16, skin, skin);
    line(ctx, 13, -14, 17, -33, 3.6, '#6b4a2b');
    circle(ctx, 17.3, -35, 4.6, '#5d4128');
  };

  // ------------------------------------------------------------ bandits and soldiers

  D.cutthroat = (ctx, o) => {
    const T = o.tc;
    legs(ctx, '#3d3a44', '#2a2420');
    torso(ctx, '#5a4a3c', -23, 6.5);
    rect(ctx, -6.5, -14, 13, 2.2, 0.8, '#2f2620', 0);
    poly(ctx, [-6.5, -23, 6.5, -23, 7.5, -18, -7.5, -18], T.main, 0.8);
    if (o.back) {
      circle(ctx, 0.5, -28.5, 5, '#3a2a22');
      poly(ctx, [-4, -30, 5, -30, 5, -27, -4, -27], T.main);
      line(ctx, -4, -28.5, -9, -26 + o.bob, 1.6, T.main);
      arm(ctx, 5.5, -20, 9, -14, '#5a4a3c', SKIN);
      return;
    }
    face(ctx, 1.3, -28.5, 5, SKIN);
    poly(ctx, [-4.5, -31.5, 5.8, -31.5, 5.8, -28.6, -4.5, -28.6], '#2f2620');
    poly(ctx, [-1, -27, 6.5, -27, 6, -24, -1, -24], T.main, 0.6);
    line(ctx, -4.5, -30, -9, -27 + o.bob, 1.6, '#2f2620');
    arm(ctx, -5.5, -20, -8, -14, '#5a4a3c', SKIN);
    arm(ctx, 5.5, -20, 10, -18, '#5a4a3c', SKIN);
    line(ctx, 10, -18, 17, -22, 1.8, '#e8eef5');
    line(ctx, 9.5, -17.5, 10.8, -19, 1.8, '#8a6a3a');
  };

  D.crossbow = (ctx, o) => {
    const T = o.tc;
    legs(ctx, '#6b6250');
    torso(ctx, '#8a8170', -24);
    rect(ctx, -4.5, -23, 9, 11, 1.5, T.main);
    rect(ctx, -7, -14, 14, 2.4, 0.8, '#4a3a28', 0);
    if (o.back) {
      circle(ctx, 0.5, -29, 5, '#e1b48e');
      ellipse(ctx, 0.5, -32, 8, 2.2, '#9aa3ad');
      rect(ctx, -3.5, -35.5, 8, 4, 2, '#9aa3ad');
      arm(ctx, 6, -21, 10, -15, '#8a8170', SKIN);
      return;
    }
    face(ctx, 1.5, -29, 4.8, SKIN);
    ellipse(ctx, 0.8, -32.3, 8.2, 2.2, '#a3acb6');
    rect(ctx, -3.5, -36, 8.5, 4.5, 2, '#a3acb6');
    arm(ctx, -5, -21, -2, -17, '#8a8170', SKIN);
    arm(ctx, 5, -21, 9, -19, '#8a8170', SKIN);
    line(ctx, -2, -18.5, 17, -19.5, 2.4, '#6a4a2a');
    line(ctx, 13, -25, 13.5, -14, 1.8, '#5a3d22');
    line(ctx, 13, -25, 4, -19, 0.6, '#d9cfb8', false);
    line(ctx, 13.5, -14, 4, -19, 0.6, '#d9cfb8', false);
    poly(ctx, [17, -20.6, 20, -19.6, 17, -18.6], '#cfd6de', 0.6);
  };

  // ------------------------------------------------------------ the dead

  D.skeleton = (ctx, o) => {
    const T = o.tc;
    skeletonBody(ctx, o);
    skull(ctx, 1, -31, 5, o.back, '#ff6a4a');
    if (o.back) {
      ellipse(ctx, -7, -20, 5.5, 7, '#6a5a44');
      arm(ctx, 4, -23, 9, -16, '#e6dfc9', '#e6dfc9');
      return;
    }
    ellipse(ctx, -7.5, -19, 5.5, 7, '#6a5a44');
    ellipse(ctx, -7.5, -19, 2.2, 2.8, T.main, 0.8);
    arm(ctx, 4, -23, 9, -17, '#e6dfc9', '#e6dfc9');
    line(ctx, 9, -17, 15, -33, 2.2, '#9d8f78');
    line(ctx, 7, -19.5, 11.5, -18, 1.8, '#6a5a44');
  };

  D.necromancer = (ctx, o) => {
    const T = o.tc;
    const pulse = 0.5 + 0.5 * Math.sin(o.t * 3);
    poly(ctx, [-7, -25, 7, -25, 11, 0, 6, -2, 2, 0, -2, -2, -6, 0, -11, 0], '#2b2230');
    rect(ctx, -2, -24, 4, 22, 1, shade(T.main, -0.3), 0);
    if (o.back) {
      poly(ctx, [-7, -34, 7, -34, 8, -20, -8, -20], '#231b28');
      poly(ctx, [-6, -34, 0, -42, 6, -34], '#231b28');
      arm(ctx, 6, -22, 10, -16, '#2b2230', '#d8d2c8');
      line(ctx, 10, -3, 12, -38, 1.8, '#3a2f2a');
      return;
    }
    poly(ctx, [-7, -33, 7, -33, 8, -19, -8, -19], '#231b28');
    poly(ctx, [-6, -33, 1, -42, 7, -33], '#231b28');
    circle(ctx, 2, -28.5, 3.8, '#120d16', 0);
    ctx.fillStyle = 'rgba(140,255,160,' + (0.6 + 0.4 * pulse) + ')';
    ctx.fillRect(2.4, -29.5, 1.4, 1.2);
    ctx.fillRect(4.6, -29.5, 1.2, 1.2);
    arm(ctx, -5.5, -21, -8, -14, '#2b2230', '#d8d2c8');
    arm(ctx, 5.5, -21, 10, -18, '#2b2230', '#d8d2c8');
    line(ctx, 11, -2, 12.5, -36, 1.8, '#3a2f2a');
    glow(ctx, 12.7, -38, 8 + pulse * 2, 'rgba(120,255,140,', 0.45);
    skull(ctx, 12.4, -38.5, 3.2, false, '#9dffad');
  };

  D.colossus = (ctx, o) => {
    const T = o.tc;
    const bone = '#ddd5bd';
    const dark = '#a99f86';
    rect(ctx, -10, -13, 7, 13, 2, dark);
    rect(ctx, 3, -13, 7, 13, 2, shade(dark, -0.1));
    ellipse(ctx, 0, -26, 14, 13, '#5c5248');
    for (let i = 0; i < 4; i++) {
      ctx.save();
      ctx.beginPath();
      ctx.ellipse(0, -26, 12 - i * 0.6, 10 - i * 2.2, 0, Math.PI * 1.05, Math.PI * 1.95);
      ctx.lineWidth = 2.8;
      ctx.strokeStyle = OUT;
      ctx.stroke();
      ctx.lineWidth = 1.6;
      ctx.strokeStyle = bone;
      ctx.stroke();
      ctx.restore();
    }
    line(ctx, 0, -38, 0, -14, 2.6, dark);
    rect(ctx, -5, -19, 10, 3, 1, T.main, 0.8);
    skull(ctx, 2, -41, 6.5, o.back, '#ff6a4a');
    poly(ctx, [-4, -45, -9, -51, -2, -47], bone, 0.8);
    poly(ctx, [7, -45, 11, -51, 5, -47], bone, 0.8);
    const sway = o.bob * 0.8;
    line(ctx, -12, -33, -17, -16, 4.4, bone);
    circle(ctx, -17.5, -14 + sway, 4.6, dark);
    line(ctx, 12, -33, 16, -17, 4.4, bone);
    circle(ctx, 16.5, -15 - sway, 4.8, dark);
  };

  D.lich = (ctx, o) => {
    const T = o.tc;
    const y = -4 + o.bob * 1.2;
    const pulse = 0.5 + 0.5 * Math.sin(o.t * 3);
    glow(ctx, 0, y - 22, 20, 'rgba(120,200,255,', 0.25 + 0.1 * pulse);
    poly(ctx, [-8, y - 26, 8, y - 26, 12, y, 7, y - 3, 3, y + 1, -1, y - 3, -5, y + 1, -9, y - 2, -12, y], '#2a3446');
    poly(ctx, [-6, y - 26, 6, y - 26, 8, y - 18, -8, y - 18], '#3a4a64', 0);
    rect(ctx, -2, y - 25, 4, 18, 1, shade(T.main, -0.25), 0);
    if (!o.back) {
      for (let i = 0; i < 3; i++) line(ctx, -4, y - 24 + i * 2.4, 4, y - 24 + i * 2.4, 0.9, '#cfc7b0', false);
    }
    skull(ctx, 1, y - 32, 5.4, o.back, '#8fe3ff');
    poly(ctx, [-4.5, y - 36, -4.5, y - 41, -2, y - 38, 1, y - 42, 4, y - 38, 6.5, y - 41, 6.5, y - 36], '#7fd3ff', 0.8);
    arm(ctx, -6, y - 23, -9, y - 15, '#2a3446', '#e6dfc9');
    arm(ctx, 6, y - 23, 10, y - 19, '#2a3446', '#e6dfc9');
    line(ctx, 11, y - 2, 12.5, y - 38, 1.8, '#4a5a70');
    glow(ctx, 12.8, y - 40, 7 + pulse * 2, 'rgba(140,220,255,', 0.6);
    poly(ctx, [12.8, y - 45, 15.5, y - 40, 12.8, y - 35, 10.1, y - 40], '#bfefff', 0.8);
  };

  // ------------------------------------------------------------ the keep, the camp and the road

  D.tower = (ctx, o) => {
    const T = o.tc;
    const stone = '#8d877d';
    poly(ctx, [-12, 0, 12, 0, 10, -34, -10, -34], stone);
    poly(ctx, [-12, 0, -1, 0, -1, -34, -10, -34], shade(stone, -0.12), 0);
    for (let r = 0; r < 4; r++) line(ctx, -11 + r * 0.5, -8 - r * 7, 11 - r * 0.5, -8 - r * 7, 0.7, 'rgba(0,0,0,0.22)', false);
    rect(ctx, -12, -40, 24, 7, 1, shade(stone, 0.06));
    for (let i = 0; i < 4; i++) rect(ctx, -12 + i * 6.6, -45, 4.4, 5.5, 0.6, shade(stone, 0.1));
    rect(ctx, 2, -27, 2.2, 7, 0.8, '#1b1714', 0);
    rect(ctx, -6, -18, 2.2, 7, 0.8, '#1b1714', 0);
    line(ctx, 0, -45, 0, -58, 1.4, '#5a3d22');
    const w = Math.sin(o.t * 3);
    poly(ctx, [0, -58, 9, -57 + w * 0.6, 9, -52 + w, 0, -51.5], T.main);
  };

  D.wall = (ctx, o) => {
    const stone = '#8f897e';
    poly(ctx, [-15, -2, 0, 5, 15, -2, 15, -20, 0, -13, -15, -20], stone);
    poly(ctx, [0, 5, 15, -2, 15, -20, 0, -13], shade(stone, -0.14), 0);
    poly(ctx, [-15, -20, 0, -27, 15, -20, 0, -13], shade(stone, 0.1));
    for (const [x, y] of [[-11, -22], [-3, -26], [5, -22], [-4, -18]]) rect(ctx, x, y - 4, 4.5, 4, 0.5, shade(stone, 0.16), 0.8);
    line(ctx, -15, -11, 0, -4, 0.7, 'rgba(0,0,0,0.25)', false);
    line(ctx, 0, -4, 15, -11, 0.7, 'rgba(0,0,0,0.25)', false);
    void o;
  };

  D.gate = (ctx, o) => {
    const T = o.tc;
    const stone = '#8f897e';
    rect(ctx, -15, -30, 6, 31, 1, stone);
    rect(ctx, 9, -30, 6, 31, 1, shade(stone, -0.12));
    rect(ctx, -16, -34, 8, 5, 1, shade(stone, 0.1));
    rect(ctx, 8, -34, 8, 5, 1, shade(stone, 0.1));
    poly(ctx, [-9, 0, 9, 0, 9, -22, 0, -28, -9, -22], '#6d4a2a');
    for (const x of [-5, 0, 5]) line(ctx, x, -1, x, -24 + Math.abs(x) * 0.6, 0.8, 'rgba(0,0,0,0.3)', false);
    rect(ctx, -9, -17, 18, 2.4, 0.5, '#3e3a36', 0.8);
    rect(ctx, -9, -7, 18, 2.4, 0.5, '#3e3a36', 0.8);
    circle(ctx, 0, -12, 1.6, '#c9a94a', 0.8);
    poly(ctx, [-8, -30, 8, -30, 6, -36, -6, -36], T.main);
  };

  D.barrel = (ctx, o) => {
    const spark = 0.5 + 0.5 * Math.sin(o.t * 14);
    rect(ctx, -7, -17, 14, 17, 4, '#7a4f28');
    rect(ctx, -7.4, -13.5, 14.8, 1.8, 0.4, '#3e3a36', 0);
    rect(ctx, -7.4, -5, 14.8, 1.8, 0.4, '#3e3a36', 0);
    ellipse(ctx, 0, -17, 7, 2.4, '#8e5f31');
    circle(ctx, 0, -9, 2.6, '#1b1714', 0);
    ctx.fillStyle = '#e8dfc4';
    ctx.fillRect(-1, -10, 2, 1.2);
    line(ctx, 2, -17.5, 4, -22, 0.9, '#3a2a1c', false);
    glow(ctx, 4, -22.5, 3 + spark * 1.5, 'rgba(255,190,80,', 0.75);
    void o;
  };

  D.cart = (ctx, o) => {
    const T = o.tc;
    const wood = '#8a5a30';
    const spin = o.t * 2;
    rect(ctx, -14, -19, 26, 9, 1.5, wood);
    rect(ctx, -14, -12, 26, 2, 0.5, shade(wood, -0.25), 0);
    for (const [x, y, w, h, c] of [[-12, -27, 8, 8, '#b98a52'], [-3, -25, 7, 6, '#d6c49a'], [4, -28, 7, 9, '#9a6a3a']]) rect(ctx, x, y, w, h, 1.5, c);
    poly(ctx, [-1, -25, 4, -25, 1.5, -29], '#e2b84c', 0.6);
    line(ctx, 12, -15, 20, -12, 1.6, shade(wood, -0.2));
    for (const wx of [-9, 6]) {
      circle(ctx, wx, -7, 6, '#5a3d22');
      circle(ctx, wx, -7, 4.2, '#7a5530', 0.8);
      for (let k = 0; k < 3; k++) {
        const a = spin + (k * Math.PI) / 3;
        line(ctx, wx - Math.cos(a) * 4, -7 - Math.sin(a) * 4, wx + Math.cos(a) * 4, -7 + Math.sin(a) * 4, 0.8, '#3a2a1c', false);
      }
      circle(ctx, wx, -7, 1.2, '#3a2a1c', 0);
    }
    line(ctx, -13, -27, -13, -38, 1.2, '#5a3d22');
    poly(ctx, [-13, -38, -6, -37, -6, -33, -13, -33.5], T.main);
  };

  // Pick-ups that lie on a tile: a war chest, a tome on a lectern, or a relic on a plinth.
  function drawLoot(ctx, kind, t) {
    const sp = Math.sin(t * 3);
    if (kind === 'chest') {
      glow(ctx, 0, -8, 16, 'rgba(255,215,110,', 0.3 + 0.1 * sp);
      rect(ctx, -10, -11, 20, 11, 1.5, '#7a4f28');
      poly(ctx, [-10, -11, 10, -11, 8, -17, -8, -17], '#8e5f31');
      rect(ctx, -10.5, -12, 21, 2.2, 0.6, '#e2b84c', 0.8);
      rect(ctx, -2, -10, 4, 4, 1, '#e2b84c', 0.8);
    } else if (kind === 'tome') {
      glow(ctx, 0, -20, 16, 'rgba(190,140,255,', 0.35 + 0.12 * sp);
      line(ctx, 0, 0, 0, -14, 2.4, '#5a3d22');
      poly(ctx, [-6, 0, 6, 0, 3, -3, -3, -3], '#5a3d22');
      poly(ctx, [-9, -14, 9, -14, 7, -18, -7, -18], '#4a2f1a');
      poly(ctx, [-8, -18, 0, -16, 0, -22, -8, -24], '#f3ead2', 0.8);
      poly(ctx, [8, -18, 0, -16, 0, -22, 8, -24], '#e9dfc3', 0.8);
      line(ctx, -6, -21, -2, -20, 0.6, '#8a7a5a', false);
      line(ctx, 2, -20, 6, -21, 0.6, '#8a7a5a', false);
    } else {
      glow(ctx, 0, -20, 15, 'rgba(200,150,255,', 0.4 + 0.12 * sp);
      poly(ctx, [-6, 0, 6, 0, 4, -8, -4, -8], '#77737e');
      const y = -18 + sp * 1.5;
      poly(ctx, [0, y - 7, 5, y, 0, y + 6, -5, y], '#b98cff', 1);
      poly(ctx, [0, y - 7, 2, y, 0, y + 6, -1, y], '#ecdcff', 0);
    }
  }

  // Height of each sprite above its feet (for health bars and hit boxes).
  const HEIGHT = {
    knight: 43, archer: 39, scout: 33, cleric: 44, berserker: 45, pyromancer: 45, assassin: 35, golem: 44,
    beastrider: 44, furgon: 44, wisp: 38, barrier: 40, enchantress: 37, witch: 47, lightning: 44, dragon: 50,
    shrub: 20, golem_king: 62, witch_queen: 60, ashen_tyrant: 82, specter: 42, warbanner: 62, cage: 31,
    mageknight: 43, skelarcher: 37, orc: 41, brute: 52, goblin_archer: 31, sapper: 31, shaman: 43, warg: 26, wolf: 22,
    spider: 25, troll: 54, cutthroat: 34, crossbow: 38, skeleton: 37, necromancer: 44, colossus: 66, lich: 60,
    drake: 42, tower: 58, castellan: 45, cart: 38, wall: 27, gate: 36, barrel: 22, warlord: 60,
  };

  const SCALE = { golem_king: 1.35, witch_queen: 1.25, ashen_tyrant: 1.6, dragon: 1.05, drake: 0.85, spider: 1.25, troll: 1.15, colossus: 1.2, lich: 1.3, warlord: 1.4, castellan: 1.05 };

  // Draw a unit with feet at the current origin. view: 'front' or 'back'.
  function drawUnit(ctx, type, team, view, t, extra) {
    const tc = TEAMS[team] || TEAMS.P;
    const o = { tc, back: view === 'back', t, bob: Math.sin(t * 2.2) * 0.7 };
    if (extra) Object.assign(o, extra);
    const sc = SCALE[type] || 1;
    if (sc !== 1) {
      ctx.save();
      ctx.scale(sc, sc);
    }
    switch (type) {
      case 'golem_king':
        D.golem(ctx, Object.assign(o, { king: true }));
        break;
      case 'witch_queen':
        D.witch(ctx, Object.assign(o, { queen: true }));
        break;
      case 'ashen_tyrant':
        D.dragon(ctx, Object.assign(o, { tyrant: true }));
        break;
      case 'drake':
        D.dragon(ctx, Object.assign(o, { drake: true }));
        break;
      case 'castellan':
        D.knight(ctx, Object.assign(o, { lord: true }));
        break;
      case 'warlord':
        D.brute(ctx, o);
        if (!o.back) poly(ctx, [-6, -40, -11, -49, -3, -43], '#d9cfb8', 0.8);
        break;
      default:
        (D[type] || D.knight)(ctx, o);
    }
    if (sc !== 1) ctx.restore();
  }

  AG.Sprites = { TEAMS, HEIGHT, drawUnit, drawLoot, shade, glow, circle, ellipse, poly, line, rect, OUT };
})(typeof window !== 'undefined' ? window : globalThis);
