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
    const body = ash ? '#3d3633' : '#8e2f24';
    const belly = ash ? '#7a5a44' : '#e3a24c';
    const wing = ash ? '#2a2422' : '#6d2119';
    const memb = ash ? '#5a2f20' : '#a8432f';
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
  };

  const SCALE = { golem_king: 1.35, witch_queen: 1.25, ashen_tyrant: 1.6, dragon: 1.05 };

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
      default:
        (D[type] || D.knight)(ctx, o);
    }
    if (sc !== 1) ctx.restore();
  }

  AG.Sprites = { TEAMS, HEIGHT, drawUnit, drawLoot, shade, glow, circle, ellipse, poly, line, rect, OUT };
})(typeof window !== 'undefined' ? window : globalThis);
