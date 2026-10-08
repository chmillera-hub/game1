// The ten scenes. Every timing is derived from the voice lines in build/timeline.json
// (via L(id) = a line, wt(id, word) = roughly when that word is spoken), so editing
// script.json and re-running keeps picture, captions, music and sound effects in sync.
const U = require('./util');
const { W, H, TAU, clamp, lerp, prog, ease, anim, pop, hash, noise, circle, ellipse, fillRR, rrect, line, text, rgba, mix, vgrad, rgrad, scaled, zoomAt, withAlpha } = U;
const C = require('./characters');
const P = require('./props');

module.exports = function makeScenes(X) {
  const { L, S, wt, talk, speaking, face, camera } = X;
  const scenes = {};

  // ---------------------------------------------------------------- shared bits
  function riley(ctx, t, x, y, s, f, extra = {}) {
    const tk = talk('riley', t), sp = speaking('riley', t);
    C.drawPerson(ctx, 'riley', Object.assign({ x, y, s, t, seed: 11 }, f, {
      open: f.mouthO > 0.05 ? 0.2 : tk.open, width: tk.width, tilt: (f.tilt || 0) + noise(t * 1.3, 1) * 0.05 * sp,
    }, extra));
  }
  function alex(ctx, t, x, y, s, f, extra = {}) {
    const tk = talk('alex', t), sp = speaking('alex', t);
    C.drawPerson(ctx, 'alex', Object.assign({ x, y, s, t, seed: 23, flip: true }, f, {
      open: tk.open, width: tk.width, tilt: (f.tilt || 0) + noise(t * 1.3, 2) * 0.05 * sp,
    }, extra));
  }
  // Riley (left) + Alex (right) at the bottom of explainer scenes
  function cast(ctx, t, rKeys, aKeys) {
    const sr = speaking('riley', t), sa = speaking('alex', t);
    circle(ctx, 270, 1282, 132, rgba('#ffd9a0', 0.55 * sr));
    circle(ctx, 810, 1282, 132, rgba('#ffd9a0', 0.55 * sa));
    riley(ctx, t, 270, 1295 - sr * 7, 0.7, face(t, rKeys));
    alex(ctx, t, 810, 1295 - sa * 7, 0.7, face(t, aKeys));
  }
  function label(ctx, str, x, y, a = 1, size = 44, color = '#5b4a3f') { text(ctx, str, x, y, { size, family: U.FONTS.hand, weight: 400, color, alpha: a }); }
  // reveal text character by character over [a, b]
  const reveal = (str, t, a, b) => str.slice(0, Math.floor(str.length * prog(t, a, b)));
  const every = (a, b, step, jitter = 0.4, seed = 1) => { const out = []; let s = a, i = 0; while (s < b) { out.push(s); s += step * (1 - jitter / 2 + hash(i++ * 7.1 + seed) * jitter); } return out; };

  // ---------------------------------------------------------------- 1. SCROLL
  const swipes = (() => {
    const a = [0, 1, 2].map((i) => wt('r_scroll', 'scroll', i) - 0.05);
    let s = a[2] + 1.05;
    while (s < L('r_comment').start - 1.7) { a.push(s); s += 1.1; }
    return a;
  })();
  const feedOffset = (t) => swipes.reduce((acc, s) => acc + 350 * ease.out(prog(t, s, s + 0.42)), 0);
  const postTap = L('r_comment').end + 0.4;

  function feedAndComposer(ctx, t, x, y, w, h) {
    const off = feedOffset(t);
    const first = Math.max(0, Math.floor(off / 350) - 1);
    for (let i = first; i < first + 4; i++) P.feedCard(ctx, x + 30, y + 84 + i * 350 - off, w - 60, P.FEED[i % P.FEED.length], t);
    const r2 = L('r_comment');
    const comp = ease.out(prog(t, r2.start - 1.3, r2.start - 0.6)) * (1 - ease.in(prog(t, postTap + 0.25, postTap + 0.6)));
    if (comp > 0) {
      const sy = lerp(y + h, y + 136, comp);
      fillRR(ctx, x, sy, w, h, 40, '#1b1d27');
      fillRR(ctx, x + w / 2 - 40, sy + 14, 80, 8, 4, '#3a3d4e');
      text(ctx, 'Add a comment', x + 40, sy + 54, { size: 30, weight: 800, color: '#8d93ab', align: 'left' });
      fillRR(ctx, x + 28, sy + 84, w - 56, 280, 26, '#262938');
      U.font(ctx, 37, 700);
      const lines = U.wrap(ctx, r2.text, w - 120);
      let budget = Math.floor(r2.text.length * prog(t, r2.start + 0.1, r2.end - 0.25));
      let lastX = x + 56, lastY = sy + 128;
      lines.forEach((ln, i) => {
        if (budget <= 0) return;
        const part = ln.slice(0, budget); budget -= ln.length + 1;
        text(ctx, part, x + 56, sy + 128 + i * 50, { size: 37, weight: 700, color: '#eef0f7', align: 'left' });
        U.font(ctx, 37, 700); lastX = x + 56 + ctx.measureText(part).width; lastY = sy + 128 + i * 50;
      });
      if (Math.floor(t * 2.5) % 2 === 0) fillRR(ctx, lastX + 4, lastY - 22, 4, 44, 2, '#7fb4ff');
      const pressed = Math.exp(-Math.pow((t - postTap) * 9, 2));
      const ready = prog(t, r2.end - 0.4, r2.end);
      scaled(ctx, x + w - 120, sy + 330, 1 - pressed * 0.15, () => {
        fillRR(ctx, -78, -28, 156, 56, 28, mix('#3a3d4e', '#4f8dff', ready));
        text(ctx, 'Post', 0, 1, { size: 30, weight: 900, color: '#fff' });
      });
      P.keyboard(ctx, x, sy + 384, w, h - 384 - 136 + 40, t, t > r2.start && t < r2.end);
    }
    const toast = U.window(t, postTap + 0.35, postTap + 2.2, 0.25);
    if (toast > 0) withAlpha(ctx, toast, () => {
      fillRR(ctx, x + 150, y + h - 170, w - 300, 90, 45, '#2e3a32');
      P.check(ctx, x + 205, y + h - 125, 0.6);
      text(ctx, 'Comment posted', x + 250, y + h - 124, { size: 32, weight: 800, color: '#d8f5e2', align: 'left' });
    });
  }

  scenes.scroll = {
    draw(ctx, t) {
      const sc = S('scroll'), r1 = L('r_scroll'), r2 = L('r_comment');
      const split = ease.inOut(prog(t, r1.start - 1.1, r1.start + 0.1)) * (1 - ease.inOut(prog(t, sc.end - 1.3, sc.end + 0.2)));
      const push = lerp(1, 1.08, ease.inOut(prog(t, sc.start, r1.start)));
      ctx.save();
      camera(ctx, lerp(push, 1.45, split), 540, lerp(1000, 1010, split), 540, lerp(1000, 1215, split));
      P.nightRoom(ctx, t);
      const typing = t > r2.start - 0.5 && t < r2.end - 0.1;
      const f = face(t, [
        [0, { lids: 0.42, brow: -0.1, browTilt: 0.55, smile: -0.12, gy: 0.75, gx: 0.05, tilt: 0.05 }],
        [r1.start + 2.6, { lids: 0.34 }, 0.8],
        [r2.start - 1.0, { lids: 0.5, gy: 0.8 }],
        [postTap + 0.4, { lids: 0.2, gy: 0.0, tilt: -0.09, smile: -0.22, browTilt: 0.75 }, 1.0],
      ]);
      riley(ctx, t, 540, 1010, 1, f, { arms: 'phone', typing, phoneScreen: '#c3d6ff', phoneTilt: Math.sin(t * 0.7) * 0.03 });
      P.couchFront(ctx);
      P.phoneGlow(ctx, 540, 1300, 1);
      ctx.restore();
      P.vignette(ctx, 0.5);
      // opening hook over the rainy establishing shot
      const hook = U.window(t, 0.5, r1.start - 1.0, 0.5);
      if (hook > 0) {
        label(ctx, 'too tired to create?', 540, 236, hook, 76, '#fff3dd');
        label(ctx, "this one's for you.", 540, 316, hook * prog(t, 1.2, 1.7), 64, '#ffd38a');
      }
      if (split > 0.001) {
        const py = lerp(-840, 232, ease.out(split));
        P.phonePanel(ctx, 150, py, 780, 770, t, (x, y, w, h) => feedAndComposer(ctx, t, x, y, w, h), { battery: 0.14 });
      }
    },
    sfx() {
      const r2 = L('r_comment');
      return [
        ...swipes.map((s) => ({ t: s, name: 'swipe', vol: 0.5 })),
        ...every(r2.start + 0.1, r2.end - 0.3, 0.11, 0.6, 3).map((s) => ({ t: s, name: 'type', vol: 0.35 })),
        { t: postTap, name: 'tap', vol: 0.8 }, { t: postTap + 0.35, name: 'pop', vol: 0.4 },
      ];
    },
  };

  // ---------------------------------------------------------------- 2. WEIGHT
  const W2 = () => {
    const rr = L('r_roof');
    return [
      { t0: wt('r_roof', 'working') - 0.3, label: 'another long shift', draw: workPanel, rot: -0.03 },
      { t0: wt('r_roof', 'roof') - 0.35, label: "rent's due. again.", draw: rentPanel, rot: 0.025 },
      { t0: wt('r_roof', 'food') - 0.35, label: 'why is everything $$$', draw: fridgePanel, rot: -0.02 },
      { t0: wt('r_roof', 'nothing') - 0.45, label: 'nothing left', draw: emptyPanel, rot: 0.02 },
    ];
  };
  function workPanel(ctx, w, h, t, t0) {
    ctx.fillStyle = '#cdd7dd'; ctx.fillRect(0, 0, w, h);
    for (let r = 0; r < 3; r++) { fillRR(ctx, 30, 70 + r * 120, 360, 14, 6, '#aab6bf'); for (let i = 0; i < 5; i++) fillRR(ctx, 44 + i * 70, 18 + r * 120, 52, 52, 6, ['#e9c46a', '#e76f51', '#8ab17d', '#a3b8c8', '#c9a6c4'][(i + r) % 5]); }
    P.wallClock(ctx, 650, 130, 74, t * 2.2, t * 26);
    C.drawPerson(ctx, 'riley', { x: w * 0.5, y: 330, s: 0.78, t, seed: 11, lids: 0.45, browTilt: 0.5, smile: -0.15, gx: -0.4, gy: 0.6, arms: 'counter' });
    ellipse(ctx, w * 0.5 + 66, 270, 7, 11, '#8fd3ff');
    fillRR(ctx, 0, h - 210, w, 210, 0, '#7b8a97');
    fillRR(ctx, 0, h - 220, w, 18, 0, '#93a2ae');
    fillRR(ctx, 560, h - 300, 160, 90, 12, '#3d4652'); fillRR(ctx, 576, h - 286, 128, 40, 6, '#9fe3b5');
    const k = ((t - t0) * 1.6) % 1;
    fillRR(ctx, lerp(40, 520, k), h - 290, 90, 70, 10, '#e9c46a');
  }
  function rentPanel(ctx, w, h, t, t0) {
    ctx.fillStyle = '#ded3c6'; ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = '#f3e7d8'; ctx.fillRect(w / 2 - 210, 210, 420, 330);
    ctx.beginPath(); ctx.moveTo(w / 2 - 260, 230); ctx.lineTo(w / 2, 40); ctx.lineTo(w / 2 + 260, 230); ctx.closePath(); ctx.fillStyle = '#a3624b'; ctx.fill();
    fillRR(ctx, w / 2 - 50, 380, 100, 160, 8, '#7a5a48'); fillRR(ctx, w / 2 - 170, 280, 90, 80, 6, '#bfe0ef'); fillRR(ctx, w / 2 + 80, 280, 90, 80, 6, '#bfe0ef');
    ctx.fillStyle = '#b7a99a'; ctx.fillRect(0, 540, w, h - 540);
    const env = [['RENT DUE', '#d64545'], ['LATE FEE', '#e07a2e'], ['ELECTRIC', '#c23b6b'], ['FINAL NOTICE', '#a12828']];
    env.forEach(([lb, c], i) => {
      const td = t0 + 0.2 + i * 0.3, k = ease.out(prog(t, td, td + 0.35));
      if (k <= 0) return;
      P.envelope(ctx, 200 + i * 140 + (i % 2) * 20, lerp(-120, h - 120 - i * 34, k), (i % 2 ? 0.12 : -0.1) * k, lb, c);
    });
  }
  function fridgePanel(ctx, w, h, t, t0) {
    ctx.fillStyle = '#d4dbe1'; ctx.fillRect(0, 0, w, h);
    fillRR(ctx, 150, 30, 420, h - 30, 24, '#eef2f4'); fillRR(ctx, 172, 52, 376, h - 60, 16, '#fbfdff');
    for (let i = 0; i < 3; i++) fillRR(ctx, 172, 200 + i * 150, 376, 10, 4, '#cfdae2');
    ellipse(ctx, 260, 470, 22, 28, '#f6efe2');
    fillRR(ctx, 420, 130, 60, 70, 10, '#e6f0f5'); fillRR(ctx, 420, 165, 60, 35, 8, '#cfe3ee');
    ctx.save(); ctx.translate(640, 220); ctx.rotate(Math.sin((t - t0) * 3) * 0.12);
    line(ctx, 0, -90, 0, -20, '#6b5b4b', 4);
    fillRR(ctx, -80, -20, 160, 90, 14, '#fff7d6');
    const flipped = t > t0 + 0.7;
    text(ctx, flipped ? '$7.89' : '$4.99', 0, 26, { size: 46, weight: 900, color: flipped ? '#d64545' : '#3d3a35' });
    if (flipped) { ctx.beginPath(); ctx.moveTo(98, 40); ctx.lineTo(98, -4); ctx.lineTo(84, 12); ctx.moveTo(98, -4); ctx.lineTo(112, 12); ctx.strokeStyle = '#d64545'; ctx.lineWidth = 7; ctx.lineCap = 'round'; ctx.stroke(); }
    ctx.restore();
  }
  function emptyPanel(ctx, w, h, t) {
    ctx.fillStyle = '#383349'; ctx.fillRect(0, 0, w, h);
    fillRR(ctx, 60, 360, w - 120, 220, 60, '#4a3d6a');
    ctx.save(); ctx.translate(250, 360); ctx.rotate(-1.35);
    C.drawPerson(ctx, 'riley', { x: 0, y: 0, s: 0.8, t, seed: 11, lids: 0.3, browTilt: 0.6, smile: -0.2, gx: 0.2, gy: 0.4, noBody: true });
    ctx.restore();
    ctx.beginPath(); ctx.moveTo(300, 330); ctx.quadraticCurveTo(500, 280, 740, 350); ctx.lineTo(740, 560); ctx.lineTo(320, 560); ctx.closePath(); ctx.fillStyle = '#b8645a'; ctx.fill();
  }
  function deskShot(ctx, t) {
    const sc = S('weight'), rd = L('r_draw'), rc = L('r_cant');
    const tCant = wt('r_cant', "can't");
    const zin = ease.inOut(prog(t, rc.start - 0.3, rc.start + 1.8)), zout = ease.inOut(prog(t, tCant + 0.2, tCant + 1.5));
    ctx.save();
    camera(ctx, lerp(1, 1.85, zin * (1 - zout)) + 0.06 * zout, 540, lerp(980, 1420, zin * (1 - zout)), 540, lerp(980, 900, zin * (1 - zout)));
    ctx.fillStyle = vgrad(ctx, 0, 1400, ['#3a3450', '#4a4262']); ctx.fillRect(-200, -200, W + 400, 1700);
    fillRR(ctx, 640, 360, 300, 230, 12, '#7a5f48'); fillRR(ctx, 652, 372, 276, 206, 8, '#a8845f');
    P.envelope(ctx, 730, 450, -0.12, 'RENT', '#d64545'); fillRR(ctx, 800, 470, 110, 80, 4, '#f3ead8');
    circle(ctx, 730, 400, 7, '#e76f51'); circle(ctx, 850, 474, 7, '#2a9d8f');
    const down = ease.inOut(prog(t, tCant + 0.5, tCant + 1.6));
    const f = face(t, [
      [0, { lids: 0.55, brow: 0.0, browTilt: 0.4, smile: -0.05, gy: 0.7, gx: 0 }],
      [rd.start - 0.3, { lids: 0.75, brow: 0.35, browTilt: 0.1, smile: 0.12 }],
      [rd.end + 0.4, { lids: 0.55, brow: 0, browTilt: 0.55, smile: -0.12 }, 0.8],
      [rc.start, { lids: 0.6, gy: 0.85 }],
      [tCant - 0.2, { lids: 0.35, browTilt: 0.8, smile: -0.25 }],
      [tCant + 0.6, { lids: 0.0 }, 0.6],
    ]);
    riley(ctx, t, 540, 930 + down * 150, 1, f, { arms: 'desk' });
    // desk + lamp + sketchbook
    ctx.beginPath(); ctx.moveTo(-100, 1330); ctx.lineTo(W + 100, 1330); ctx.lineTo(W + 100, 2000); ctx.lineTo(-100, 2000); ctx.closePath(); ctx.fillStyle = '#7d5a44'; ctx.fill();
    ctx.fillStyle = '#946b51'; ctx.fillRect(-100, 1330, W + 200, 16);
    ctx.save(); ctx.globalCompositeOperation = 'screen';
    ctx.fillStyle = rgrad(ctx, 230, 1200, 600, [[0, 'rgba(255,190,110,0.45)'], [1, 'rgba(255,190,110,0)']]); ctx.fillRect(-370, 600, 1200, 1200); ctx.restore();
    fillRR(ctx, 150, 1300, 150, 30, 12, '#2f2a3d'); line(ctx, 225, 1300, 180, 1120, '#2f2a3d', 12); line(ctx, 180, 1120, 270, 1040, '#2f2a3d', 12);
    ctx.beginPath(); ctx.moveTo(230, 1000); ctx.lineTo(340, 1030); ctx.lineTo(300, 1110); ctx.lineTo(200, 1080); ctx.closePath(); ctx.fillStyle = '#e8b04a'; ctx.fill();
    ctx.beginPath(); ctx.moveTo(330, 1360); ctx.lineTo(750, 1360); ctx.lineTo(820, 1560); ctx.lineTo(260, 1560); ctx.closePath(); ctx.fillStyle = '#fbf8f2'; ctx.fill();
    line(ctx, 540, 1360, 540, 1560, '#e2dccf', 4);
    for (let i = 0; i < 9; i++) circle(ctx, 352 + i * 50, 1364, 6, '#7a7488');
    if (down > 0) { // arms folded on the desk, face buried
      const ay = lerp(1260, 1112, down);
      fillRR(ctx, 300, ay, 300, 116, 58, '#2f6f79'); circle(ctx, 590, ay + 58, 40, '#93603f');
      fillRR(ctx, 480, ay + 16, 300, 116, 58, '#3e8c98'); circle(ctx, 490, ay + 74, 40, '#b07650');
    }
    // pencil: lifts, hovers, then drops and rolls
    const tDrop = tCant + 0.05, drop = ease.in(prog(t, tDrop, tDrop + 0.35));
    const hover = prog(t, rd.start, rd.start + 0.6);
    const tremble = Math.sin(t * 40) * 3 * prog(t, rc.start, tDrop);
    const px = lerp(610, 640, drop) + tremble, py = lerp(lerp(1300, 1230, hover), 1480, drop);
    ctx.save(); ctx.translate(px, py); ctx.rotate(lerp(-0.5, 1.4, drop));
    fillRR(ctx, -9, -90, 18, 120, 4, '#f2c14e'); ctx.beginPath(); ctx.moveTo(-9, 30); ctx.lineTo(9, 30); ctx.lineTo(0, 52); ctx.closePath(); ctx.fillStyle = '#e8cfa8'; ctx.fill(); fillRR(ctx, -9, -104, 18, 16, 4, '#e76f51');
    ctx.restore();
    ctx.restore();
    P.vignette(ctx, 0.55);
  }
  scenes.weight = {
    draw(ctx, t) {
      const rr = L('r_roof'), rc = L('r_cant');
      const panels = W2();
      deskShot(ctx, t);
      const mIn = panels[0].t0 - 0.4, mOut = rc.start - 0.35;
      const wipeIn = ease.inOut(prog(t, mIn, mIn + 0.45)), wipeOut = ease.inOut(prog(t, mOut, mOut + 0.45));
      if (wipeIn <= 0 || wipeOut >= 1) return;
      ctx.save();
      ctx.beginPath(); ctx.rect(W * (1 - wipeIn), 0, W * (wipeIn - wipeOut), H); ctx.clip();
      ctx.translate(-W * wipeOut * 0, 0);
      ctx.fillStyle = '#e3dbd0'; ctx.fillRect(0, 0, W, H);
      panels.forEach((p, i) => {
        const nx = panels[i + 1];
        const kin = ease.out(prog(t, p.t0, p.t0 + 0.45)), kout = nx ? ease.in(prog(t, nx.t0, nx.t0 + 0.4)) : 0;
        if (kin <= 0 || kout >= 1) return;
        const ox = (1 - kin) * 1150 - kout * 1150;
        P.photoFrame(ctx, 110 + ox, 410, 860, 880, p.rot, (w, h) => p.draw(ctx, w, h, t, p.t0), p.label);
      });
      const lvl = lerp(0.62, 0.03, ease.inOut(prog(t, rr.start, wt('r_roof', 'nothing') + 0.3)));
      label(ctx, 'energy', 300, 262, 1, 52, '#4a4048');
      P.battery(ctx, 600, 262, 0.75, lvl, t);
      P.vignette(ctx, 0.35);
      ctx.restore();
    },
    sfx() {
      const p = W2(), rc = L('r_cant'), tCant = wt('r_cant', "can't");
      const ev = [{ t: p[0].t0 - 0.4, name: 'whoosh', vol: 0.5 }];
      p.forEach((x, i) => { if (i) ev.push({ t: x.t0, name: 'whoosh', vol: 0.35 }); });
      for (let i = 0; i < 4; i++) ev.push({ t: p[1].t0 + 0.2 + i * 0.3 + 0.33, name: 'thud', vol: 0.55 });
      ev.push(...every(p[0].t0 + 0.3, p[1].t0, 0.62, 0.1, 9).map((s) => ({ t: s, name: 'beep', vol: 0.25 })));
      ev.push({ t: p[2].t0 + 0.7, name: 'tick', vol: 0.5 });
      ev.push({ t: rc.start - 0.35, name: 'whoosh', vol: 0.4 });
      ev.push({ t: tCant + 0.4, name: 'clatter', vol: 0.7 });
      return ev;
    },
  };

  // ---------------------------------------------------------------- 3. REPLY
  function replyPanelContent(ctx, t, x, y, w, h) {
    const sc = S('reply'), ah = L('a_hey'), as = L('a_show');
    const b1 = sc.start + 0.5;
    // the comment thread
    const yy = y + 110;
    fillRR(ctx, x + 30, yy, w - 60, 250, 28, '#1f2230');
    circle(ctx, x + 84, yy + 56, 30, '#3e8c98');
    C.drawPerson(ctx, 'riley', { x: x + 84, y: yy + 62, s: 0.26, t, seed: 11, noBody: true, lids: 0.6 });
    text(ctx, 'riley', x + 130, yy + 56, { size: 30, weight: 800, color: '#cfd3e0', align: 'left' });
    U.font(ctx, 29, 650);
    U.wrap(ctx, 'Social media is getting so drab. I\'ve always wanted to make something that means something to me... but I\'m just so tired.', w - 120)
      .forEach((ln, i) => text(ctx, ln, x + 60, yy + 112 + i * 40, { size: 29, weight: 650, color: '#a9aec2', align: 'left' }));
    const rk = ease.out(prog(t, b1 + 0.8, b1 + 1.3));
    if (rk > 0) withAlpha(ctx, rk, () => {
      const ry = yy + 280 + (1 - rk) * 40;
      line(ctx, x + 70, yy + 250, x + 70, ry + 60, '#2f3346', 5);
      fillRR(ctx, x + 100, ry, w - 130, 200, 28, '#262a3a');
      circle(ctx, x + 152, ry + 56, 30, '#ffe0b0');
      C.drawPerson(ctx, 'alex', { x: x + 152, y: ry + 62, s: 0.26, t, seed: 23, noBody: true, smile: 0.4 });
      text(ctx, 'alex', x + 198, ry + 56, { size: 30, weight: 800, color: '#ffd38a', align: 'left' });
      text(ctx, 'Hey. I saw your comment.', x + 130, ry + 112, { size: 29, weight: 650, color: '#d9dcea', align: 'left' });
      text(ctx, 'And honestly? I\'ve been there...', x + 130, ry + 152, { size: 29, weight: 650, color: '#d9dcea', align: 'left' });
    });
    P.notification(ctx, x + 24, y + 80, w - 48, b1, t, b1 + 1.7);
    // warm video reply from Alex
    const m = ease.inOut(prog(t, ah.start - 0.7, ah.start - 0.05));
    if (m > 0) withAlpha(ctx, m, () => {
      ctx.fillStyle = vgrad(ctx, y, y + h, ['#ffe9c9', '#ffd3a1']); ctx.fillRect(x - 600, y - 1200, w + 1200, h + 2400);
      for (let i = 0; i < 6; i++) circle(ctx, x + hash(i * 3) * w, y + hash(i * 5) * h * 0.8 + Math.sin(t + i) * 10, 40 + hash(i) * 50, rgba('#fff3dd', 0.6));
      const fa = face(t, [
        [0, { lids: 0.9, smile: 0.35, gx: 0.1, gy: 0.2, arms: 'wave', brow: 0.2 }],
        [ah.start + 1.0, { arms: 'down', browTilt: 0.35, smile: 0.25 }],
        [as.start, { arms: 'palm', browTilt: 0, smile: 0.45, brow: 0.3 }],
        [as.end + 0.3, { arms: 'down', smile: 0.5, squint: 0.2 }],
      ]);
      alex(ctx, t, x + w / 2, y + h * 0.55 + (1 - m) * 60, 1.0, fa, { flip: false });
    });
  }
  scenes.reply = {
    draw(ctx, t) {
      const sc = S('reply'), ah = L('a_hey'), as = L('a_show'), ro = L('r_ok');
      const b1 = sc.start + 0.5, b2 = sc.start + 1.0;
      const split = ease.inOut(prog(t, sc.start + 0.9, sc.start + 1.8));
      const expand = ease.inOut(prog(t, sc.end - 1.0, sc.end + 0.3));
      const buzz = Math.max(...[b1, b2].map((b) => (t > b && t < b + 0.35 ? 1 : 0)));
      ctx.save();
      camera(ctx, lerp(1.0, 1.45, split), 540, lerp(1000, 1010, split), 540, lerp(1000, 1215, split));
      P.nightRoom(ctx, t, { clockMin: 52 });
      const f = face(t, [
        [0, { lids: 0.18, gy: 0.75, browTilt: 0.6, smile: -0.18, tilt: -0.07 }],
        [b1 + 0.1, { lids: 0.55, brow: 0.2, tilt: -0.02 }, 0.3],
        [sc.start + 1.4, { lids: 0.88, gy: -0.8, gx: 0, brow: 0.4, tilt: 0 }, 0.5],
        [ah.start + 1.2, { browTilt: 0.3, smile: -0.02 }],
        [as.end - 1.2, { smile: 0.14, lids: 0.92, brow: 0.45, browTilt: 0.1 }],
        [ro.start - 0.25, { smile: 0.32, tilt: 0.05 }],
        [ro.end + 0.15, { smile: 0.45, squint: 0.2, tilt: 0.0 }],
      ]);
      riley(ctx, t, 540, 1010, 1, f, { arms: 'phone', phoneScreen: t > b1 ? '#e6eeff' : '#8ea6d6', phoneTilt: Math.sin(t * 70) * 0.07 * buzz });
      P.couchFront(ctx);
      P.phoneGlow(ctx, 540, 1300, t > b1 ? 1.35 : 0.6);
      ctx.restore();
      P.vignette(ctx, 0.5);
      if (split > 0.001) {
        const py = lerp(-840, 232, ease.out(split));
        const rx = lerp(150, -20, expand), ry = lerp(py, -20, expand), rw = lerp(780, W + 40, expand), rh = lerp(770, H + 40, expand);
        const warm = prog(t, ah.start - 0.7, ah.start);
        P.phonePanel(ctx, rx, ry, rw, rh, t, (x, y, w, h) => replyPanelContent(ctx, t, x, y + (h - 770) * 0.3, w, 770), { battery: 0.12, bg: warm >= 1 ? '#ffe2b8' : '#14161f', clock: '11:52' });
      }
    },
    sfx() {
      const sc = S('reply'), b1 = sc.start + 0.5, b2 = sc.start + 1.0;
      return [{ t: b1, name: 'buzz', vol: 0.7 }, { t: b2, name: 'buzz', vol: 0.6 }, { t: b1 + 0.05, name: 'ping', vol: 0.55 },
        { t: L('a_hey').start - 0.6, name: 'chime', vol: 0.5 }, { t: sc.end - 1.0, name: 'whoosh', vol: 0.4 }];
    },
  };

  // ---------------------------------------------------------------- step scenes
  function stepFrame(ctx, t, id, n, title, visual, rKeys, aKeys) {
    P.warmBG(ctx, t);
    ctx.save(); ctx.translate(0, 38); zoomAt(ctx, 540, 715, 1.08, () => visual(ctx, t)); ctx.restore();
    P.stepTitle(ctx, n, title, t, S(id).start + 0.25);
    cast(ctx, t, rKeys, aKeys);
  }
  const titleSfx = (id) => [{ t: S(id).start + 0.25, name: 'pop', vol: 0.5 }];

  // ---------------------------------------------------------------- 4. STEP 1
  function step1Visual(ctx, t) {
    const a = L('a_s1a'), b = L('a_s1b'), r = L('r_s1'), c = L('a_s1c');
    const tSpark = wt('a_s1a', 'spark'), items = [[wt('a_s1a', 'feeling'), 215, 480, 'a feeling'], [wt('a_s1a', 'memory'), 865, 480, 'a memory'], [wt('a_s1a', 'what if'), 540, 925, 'a "what if..."']];
    const shrink = ease.inOut(prog(t, b.start - 0.2, b.start + 0.5)), toPol = ease.inOut(prog(t, r.start - 0.3, r.start + 0.6));
    const tStick = wt('a_s1b', 'sticks') - 0.2;
    let on = anim(t, tSpark - 0.1, 0.25);
    if (t > tSpark - 0.1 && t < tSpark + 0.45) on *= Math.sin(t * 70) > -0.3 ? 1 : 0.35;
    on = Math.min(1.25, on + 0.5 * Math.exp(-Math.pow((t - tStick - 0.75) * 4, 2)));
    const bx = 540, by = lerp(650, 560, shrink), bs = lerp(1, 0.62, shrink) * (1 - toPol) * pop(t, a.start - 0.3, 0.5);
    if (bs > 0.01) P.lightbulb(ctx, bx, by, bs, Math.min(1, on), t);
    items.forEach(([ti, x, y, lb], i) => {
      const k = pop(t, ti - 0.1) * (1 - toPol), al = 1 - 0.7 * shrink;
      if (k <= 0) return;
      withAlpha(ctx, al, () => scaled(ctx, x, y, k * lerp(1, 0.8, shrink), () => {
        circle(ctx, 0, 0, 118, rgba('#ffffff', 0.9));
        if (i === 0) P.heartCloud(ctx, 0, -6, 0.95, t);
        if (i === 1) P.polaroid(ctx, 0, -4, 0.42, t, 0.08, { label: ' ' });
        if (i === 2) P.catAstronaut(ctx, 0, -4, 0.95, t);
        label(ctx, lb, 0, 150);
      }));
    });
    const pin = ease.out(prog(t, b.start + 0.4, b.start + 0.9)), pout = ease.in(prog(t, r.start - 0.5, r.start - 0.1));
    if (pin > 0 && pout < 1) P.socialPost(ctx, 120 + (1 - pin) * 1000 - pout * 1150, 740, 840, t);
    const sp = prog(t, tStick, tStick + 0.75);
    if (sp > 0 && sp < 1) {
      const x = lerp(540, bx, sp), y = lerp(780, by, ease.out(sp)) - Math.sin(sp * Math.PI) * 140;
      for (let i = 1; i < 5; i++) P.sparkle(ctx, x - i * 18 * (1 - sp), y + i * 22, 16 - i * 3, rgba('#ffc94d', 0.7), t * 5);
      P.sparkle(ctx, x, y, 36, '#ffb52e', t * 6);
    }
    if (toPol > 0) P.polaroid(ctx, 540, 700, lerp(0.42, 1.4, toPol), t, lerp(0.15, -0.04, toPol), { label: 'grandma + me' });
    const ck = pop(t, c.start + 0.15);
    if (ck > 0) {
      P.check(ctx, 748, 470, 1.25, ck);
      for (let i = 0; i < 6; i++) { const a2 = i / 6 * TAU + t; P.sparkle(ctx, 540 + Math.cos(a2) * 260 * ck, 690 + Math.sin(a2) * 300 * ck, 18, rgba('#ffc94d', 1 - prog(t, c.start + 0.5, c.start + 1.8)), t * 4); }
    }
  }
  scenes.step1 = {
    draw(ctx, t) {
      const a = L('a_s1a'), b = L('a_s1b'), r = L('r_s1'), c = L('a_s1c');
      stepFrame(ctx, t, 'step1', 1, 'Find a spark', step1Visual,
        [[0, { lids: 0.85, gx: 0.2, gy: -0.6, smile: 0.08, brow: 0.15, arms: 'down' }],
          [b.start, { gx: 0.35, gy: -0.3 }],
          [r.start - 0.6, { arms: 'chin', gx: -0.5, gy: -0.75, lids: 0.72, smile: 0.25, shine: 0.35, browTilt: 0.3 }],
          [r.start + 1.8, { gx: 0.25, gy: -0.55 }],
          [c.start, { arms: 'down', smile: 0.5, squint: 0.25, gx: 0.9, gy: 0, shine: 0.2, browTilt: 0 }]],
        [[0, { lids: 0.9, gx: -0.4, gy: -0.5, smile: 0.35, arms: 'down' }],
          [a.start + 0.2, { arms: 'point', gy: -0.7 }],
          [b.start, { arms: 'palm', gx: -0.3, gy: -0.4 }],
          [r.start - 0.3, { arms: 'down', gx: -1, gy: 0.1, smile: 0.3, browTilt: 0.2 }],
          [c.start - 0.1, { smile: 0.7, squint: 0.3, tilt: -0.05, browTilt: 0 }]]);
    },
    sfx() {
      const b = L('a_s1b'), c = L('a_s1c'), tStick = wt('a_s1b', 'sticks') - 0.2;
      return [...titleSfx('step1'), { t: wt('a_s1a', 'spark') - 0.1, name: 'spark', vol: 0.6 },
        ...['feeling', 'memory', 'what if'].map((w) => ({ t: wt('a_s1a', w) - 0.1, name: 'pop', vol: 0.4 })),
        { t: b.start + 0.4, name: 'whoosh', vol: 0.35 }, { t: tStick, name: 'sparkle', vol: 0.5 },
        { t: L('r_s1').start - 0.3, name: 'whoosh', vol: 0.3 }, { t: c.start + 0.15, name: 'ding', vol: 0.5 }];
    },
  };

  // ---------------------------------------------------------------- 5. STEP 2
  const RAMBLE = 'ok so... my grandma. her tiny kitchen, steam everywhere. she folded dumplings SO fast and laughed at my lumpy ones. i miss her';
  const SCRIPT = [
    ['THE DUMPLING LESSON', '#3b3355', 700, 42],
    ['SCENE 1: a tiny, steamy kitchen.', '#6b6385', 600, 33],
    ['GRANDMA folds a perfect dumpling.', '#6b6385', 600, 33],
    ['LITTLE RILEY tries. It\'s lumpy.', '#6b6385', 600, 33],
    ['GRANDMA (laughing):', '#c4553f', 800, 33],
    ['"Gently... like you\'re tucking', '#3b3355', 700, 33],
    ['  it into bed."', '#3b3355', 700, 33],
  ];
  function step2Visual(ctx, t) {
    const a = L('a_s2a'), b = L('a_s2b');
    const win = pop(t, S('step2').start + 0.4, 0.5);
    zoomAt(ctx, 540, 710, win, () => {
      P.chatWindow(ctx, 110, 370, 860, 690, 'Chatbot');
      ctx.save(); ctx.beginPath(); ctx.rect(110, 462, 860, 598); ctx.clip();
      const up = 330 * ease.inOut(prog(t, b.start - 1.2, b.start - 0.5));
      U.font(ctx, 32, 650);
      const lines = U.wrap(ctx, RAMBLE, 560);
      const kk = prog(t, a.start + 0.9, a.end + 1.6);
      if (kk > 0) {
        let budget = Math.floor(RAMBLE.length * kk);
        const shown = lines.map((ln) => { const s = ln.slice(0, Math.max(0, budget)); budget -= ln.length + 1; return s; }).filter(Boolean);
        P.bubble(ctx, 340, 500 - up, 600, shown.length ? shown : [' '], { size: 32, bg: '#3e8c98' });
      }
      const dots = U.window(t, b.start - 1.0, b.start + 0.1, 0.15);
      if (dots > 0) withAlpha(ctx, dots, () => P.typingDots(ctx, 150, 860 - up, t));
      const dk = ease.back(prog(t, b.start, b.start + 0.5));
      if (dk > 0) zoomAt(ctx, 540, 820, dk, () => {
        fillRR(ctx, 140, 590, 800, 460, 26, '#f3eefc');
        fillRR(ctx, 158, 608, 764, 424, 20, '#ffffff');
        SCRIPT.forEach(([s, col, wgt, size], i) => {
          const ti = b.start + 0.3 + i * (b.dur / SCRIPT.length);
          const k2 = ease.out(prog(t, ti, ti + 0.3));
          if (k2 > 0) text(ctx, s, 186 + (1 - k2) * 30, 650 + i * 56, { size, weight: wgt, color: col, align: 'left', alpha: k2, family: i === 0 ? U.FONTS.title : U.FONTS.ui });
        });
      });
      ctx.restore();
    });
  }
  scenes.step2 = {
    draw(ctx, t) {
      const a = L('a_s2a'), b = L('a_s2b'), r = L('r_s2');
      stepFrame(ctx, t, 'step2', 2, 'Turn it into a script', step2Visual,
        [[0, { gx: 0.2, gy: -0.6, smile: 0.1, arms: 'down' }],
          [a.start + 0.5, { arms: 'phone', typing: true, gy: 0.75, gx: 0, lids: 0.8, smile: 0.18 }],
          [a.end + 1.6, { arms: 'down', typing: false, gy: -0.6, gx: 0.25, lids: 0.9 }],
          [r.start - 0.6, { lids: 1, brow: 0.85, mouthO: 0.7, gx: 0.15, gy: -0.7 }, 0.3],
          [r.start + 0.15, { mouthO: 0 }, 0.2],
          [r.end - 0.3, { smile: 0.6, squint: 0.3, brow: 0.5 }]],
        [[0, { gx: -1, gy: 0, smile: 0.4, arms: 'down' }],
          [a.start + 2.4, { arms: 'palm', gx: -0.5, gy: -0.3 }],
          [b.start, { arms: 'down', gx: -0.4, gy: -0.7 }],
          [r.start, { gx: -1, gy: 0, smile: 0.65, squint: 0.25 }]]);
    },
    sfx() {
      const a = L('a_s2a'), b = L('a_s2b');
      return [...titleSfx('step2'), { t: S('step2').start + 0.4, name: 'pop', vol: 0.35 },
        ...every(a.start + 0.9, a.end + 1.6, 0.1, 0.6, 5).map((s) => ({ t: s, name: 'type', vol: 0.3 })),
        { t: a.end + 1.7, name: 'send', vol: 0.5 }, { t: b.start, name: 'pop', vol: 0.45 },
        ...SCRIPT.map((_, i) => ({ t: b.start + 0.3 + i * (b.dur / SCRIPT.length), name: 'tick', vol: 0.2 })),
        { t: L('r_s2').end - 0.2, name: 'sparkle', vol: 0.3 }];
    },
  };

  // ---------------------------------------------------------------- 6. STEP 3
  const PROMPT = 'turn my script into an animated video, please!';
  function step3Visual(ctx, t) {
    const a = L('a_s3a'), b = L('a_s3b'), c = L('a_s3c'), r2 = L('r_s3b'), d = L('a_s3d');
    const win = pop(t, S('step3').start + 0.4, 0.5);
    const tPaste = wt('a_s3a', 'paste') - 0.1, tAsk = wt('a_s3a', 'ask it');
    const tCode = wt('a_s3b', 'writes') - 0.15, tDraw = wt('a_s3b', 'draws') - 0.1, tVoice = wt('a_s3b', 'voices') - 0.15, tMusic = wt('a_s3b', 'music') - 0.15, tTog = wt('a_s3b', 'together') - 0.2;
    const tRuns = wt('a_s3c', 'runs') - 0.2;
    zoomAt(ctx, 540, 700, win, () => {
      P.termWindow(ctx, 90, 370, 900, 670, 'AI coding assistant');
      ctx.save(); ctx.beginPath(); ctx.rect(90, 434, 900, 606); ctx.clip();
      // phase 1: paste + prompt
      const p1 = 1 - ease.inOut(prog(t, tCode - 0.3, tCode));
      if (p1 > 0) withAlpha(ctx, p1, () => {
        const pk = pop(t, tPaste);
        if (pk > 0) scaled(ctx, 300, 560, pk, () => {
          fillRR(ctx, -170, -80, 340, 160, 18, '#2f2a45');
          fillRR(ctx, -150, -62, 130, 36, 10, '#ffb347'); text(ctx, 'script.txt', -85, -43, { size: 22, weight: 800, color: '#2d2a3e', family: U.FONTS.mono });
          for (let i = 0; i < 3; i++) fillRR(ctx, -150, -8 + i * 26, 280 - i * 50, 12, 6, '#4d4670');
        });
        const pr = reveal(PROMPT, t, tAsk, a.end - 0.1);
        if (t > tAsk - 0.3) {
          text(ctx, '>', 130, 720, { size: 34, weight: 700, color: '#06d6a0', family: U.FONTS.mono, align: 'left' });
          U.font(ctx, 32, 500, U.FONTS.mono);
          U.wrap(ctx, pr, 760).forEach((ln, i) => text(ctx, ln, 170, 720 + i * 48, { size: 32, weight: 500, color: '#e8e4ff', family: U.FONTS.mono, align: 'left' }));
        }
      });
      // phase 2: assembly
      const p2 = ease.inOut(prog(t, tCode - 0.3, tCode)) * (1 - ease.inOut(prog(t, c.start - 0.3, c.start + 0.1)));
      if (p2 > 0) withAlpha(ctx, p2, () => {
        P.codeLines(ctx, 130, 480, 8, 25, Math.floor(prog(t, tCode, tDraw + 0.4) * 260));
        const gk = pop(t, tDraw);
        if (gk > 0) scaled(ctx, 300, 900, gk, () => {
          circle(ctx, 0, -20, 150, rgba('#ffe9c7', 0.25));
          const talkFake = t > tVoice && t < tTog ? Math.abs(noise(t * 9, 4)) : 0;
          C.drawPerson(ctx, 'grandma', { x: 0, y: -40, s: 0.55, t, seed: 8, lids: 0.75 * prog(t, tDraw + 0.3, tDraw + 0.5), smile: 0.6, open: talkFake, gx: 0.4 });
        });
        if (t > tVoice) withAlpha(ctx, prog(t, tVoice, tVoice + 0.3), () => P.waveform(ctx, 440, 790, 300, 90, t, t < tTog + 0.5 ? 1 : 0.4));
        if (t > tMusic) for (let i = 0; i < 4; i++) { const p = ((t - tMusic) * 0.45 + i * 0.25) % 1; P.note(ctx, 760 + i * 40 + Math.sin(t * 2 + i) * 20, 960 - p * 330, 0.7, rgba(['#ffd166', '#ff8fa3', '#9fe3b5', '#b9a8ff'][i], 1 - p)); }
        const fk = ease.out(prog(t, tTog, tTog + 0.5));
        if (fk > 0) P.filmStrip(ctx, lerp(1000, 130, fk), 960, 820, 76, ['#f6d9a5', '#bfe3f2', '#ffd3a1', '#f3e3c3', '#c9e4c5', '#ffd166'], t);
        const ck = pop(t, tTog + 0.75);
        if (ck > 0) { P.fileCard(ctx, 610, 700, 1.15, 'dumpling_lesson.mp4', ck); P.check(ctx, 780, 590, 0.9, pop(t, tTog + 1.0)); }
      });
      // phase 3: no editing software; the bot runs the tools
      const p3 = ease.inOut(prog(t, c.start - 0.1, c.start + 0.3)) * (1 - ease.inOut(prog(t, r2.start - 0.2, r2.start + 0.3)));
      if (p3 > 0) withAlpha(ctx, p3, () => {
        const suck = ease.in(prog(t, tRuns, tRuns + 0.5));
        if (suck < 1) scaled(ctx, lerp(540, 820, suck), lerp(700, 900, suck), 1 - suck, () => {
          fillRR(ctx, -360, -200, 720, 400, 22, '#3a3554');
          for (let r = 0; r < 6; r++) for (let i = 0; i < 7; i++) if (hash(r * 9 + i) > 0.3) fillRR(ctx, -330 + i * 92 + hash(r * 3 + i) * 30, -160 + r * 52, 40 + hash(r + i * 7) * 60, 34, 8, ['#ff8fa3', '#ffd166', '#9fe3b5', '#82aaff', '#c792ea'][(r + i) % 5]);
          text(ctx, 'editing software?', 0, 250, { size: 48, family: U.FONTS.hand, weight: 400, color: '#e8e4ff' });
        });
        const ok = ease.out(prog(t, tRuns, tRuns + 0.6));
        if (ok > 0) {
          const icons = ['film', 'note', 'mic', 'brush', 'wrench'];
          icons.forEach((ic, i) => {
            const ang = i / icons.length * TAU + t * 1.3, rx = 270 * ok, ry = 170 * ok;
            const x = 540 + Math.cos(ang) * rx, y = 740 + Math.sin(ang) * ry;
            circle(ctx, x, y, 44, ['#ffd166', '#ff8fa3', '#9fe3b5', '#82aaff', '#c792ea'][i]);
            toolIcon(ctx, ic, x, y);
          });
        }
      });
      // phase 4: plain words in, code out
      const p4 = ease.inOut(prog(t, d.start - 0.1, d.start + 0.4));
      if (p4 > 0) withAlpha(ctx, p4, () => {
        P.bubble(ctx, 130, 520, 420, ['make grandma', 'smile more :)'], { size: 40, bg: '#3e8c98', weight: 800 });
        const ar = ease.out(prog(t, wt('a_s3d', 'handles') - 0.4, wt('a_s3d', 'handles')));
        if (ar > 0) {
          line(ctx, 580, 620, lerp(580, 700, ar), 620, '#ffd166', 10);
          if (ar > 0.9) { ctx.beginPath(); ctx.moveTo(712, 620); ctx.lineTo(690, 600); ctx.lineTo(690, 640); ctx.closePath(); ctx.fillStyle = '#ffd166'; ctx.fill(); }
          withAlpha(ctx, ar, () => { fillRR(ctx, 730, 560, 230, 120, 16, '#2f2a45'); text(ctx, 'smile:', 760, 600, { size: 28, color: '#d6deeb', family: U.FONTS.mono, align: 'left', weight: 500 }); text(ctx, '0.4 → 0.9', 760, 642, { size: 28, color: '#f78c6c', family: U.FONTS.mono, align: 'left', weight: 600 }); });
        }
        label(ctx, 'plain words in. code out.', 540, 820, ar, 52, '#e8e4ff');
      });
      ctx.restore();
      // the helper bot lives in the corner once it starts working
      const bk = pop(t, a.end - 0.5);
      if (bk > 0) {
        const center = ease.inOut(prog(t, c.start + 0.1, c.start + 0.6)) * (1 - ease.inOut(prog(t, r2.start - 0.2, r2.start + 0.4)));
        C.drawBot(ctx, lerp(870, 540, center), lerp(940, 740, center), bk * lerp(0.8, 1.25, center), t,
          { working: t > tCode && t < tTog + 0.8, happy: (t > tTog + 0.8 && t < c.start) || t > tRuns, look: t < tCode ? [-0.8, -0.2] : [-0.5, -0.4], glow: center });
      }
    });
  }
  function toolIcon(ctx, ic, x, y) {
    ctx.save(); ctx.translate(x, y); ctx.strokeStyle = '#2d2a3e'; ctx.fillStyle = '#2d2a3e'; ctx.lineWidth = 6; ctx.lineCap = 'round';
    if (ic === 'film') { fillRR(ctx, -22, -16, 44, 32, 5, '#2d2a3e'); for (let i = 0; i < 3; i++) fillRR(ctx, -16 + i * 13, -12, 7, 5, 1, '#fff'); }
    if (ic === 'note') P.note(ctx, -14, 12, 0.42, '#2d2a3e');
    if (ic === 'mic') { fillRR(ctx, -9, -24, 18, 30, 9, '#2d2a3e'); ctx.beginPath(); ctx.arc(0, 0, 15, 0.2, Math.PI - 0.2); ctx.stroke(); line(ctx, 0, 15, 0, 24, '#2d2a3e', 5); }
    if (ic === 'brush') { ctx.rotate(0.7); fillRR(ctx, -5, -26, 10, 32, 4, '#2d2a3e'); ellipse(ctx, 0, 14, 9, 13, '#2d2a3e'); }
    if (ic === 'wrench') { ctx.rotate(-0.7); fillRR(ctx, -5, -10, 10, 36, 4, '#2d2a3e'); circle(ctx, 0, -16, 13, '#2d2a3e'); circle(ctx, 0, -22, 6, '#82aaff'); }
    ctx.restore();
  }
  scenes.step3 = {
    draw(ctx, t) {
      const a = L('a_s3a'), b = L('a_s3b'), c = L('a_s3c'), r = L('r_s3'), r2 = L('r_s3b'), d = L('a_s3d');
      stepFrame(ctx, t, 'step3', 3, 'Ask for the video', step3Visual,
        [[0, { gx: 0.2, gy: -0.6, smile: 0.1, arms: 'down' }],
          [b.start, { lids: 0.95, brow: 0.3, gx: 0.1 }],
          [wt('a_s3b', 'together'), { brow: 0.5, smile: 0.25 }],
          [r.start - 0.4, { arms: 'gasp', lids: 1, brow: 0.9, mouthO: 0.7 }, 0.3],
          [r.end + 0.15, { arms: 'down', mouthO: 0, brow: 0.3 }],
          [r2.start - 0.3, { browTilt: 0.7, brow: 0.05, smile: -0.25, gx: 0.9, gy: 0.1, lids: 0.8 }],
          [d.start + 1.4, { browTilt: 0.2, smile: 0.15, gx: 0.3, gy: -0.6 }],
          [d.end - 0.6, { smile: 0.45, browTilt: 0, brow: 0.3, lids: 0.9 }]],
        [[0, { gx: -0.4, gy: -0.6, smile: 0.35, arms: 'down' }],
          [a.start + 0.3, { arms: 'point', gy: -0.7 }],
          [b.start + 0.3, { arms: 'palm' }],
          [c.start, { arms: 'down' }],
          [r.start, { gx: -1, gy: 0, smile: 0.6, squint: 0.2 }],
          [r2.end, { smile: 0.5, arms: 'palm', brow: 0.2, squint: 0 }],
          [d.end, { arms: 'down' }]]);
    },
    sfx() {
      const a = L('a_s3a'), c = L('a_s3c'), d = L('a_s3d');
      const tAsk = wt('a_s3a', 'ask it'), tCode = wt('a_s3b', 'writes') - 0.15, tTog = wt('a_s3b', 'together') - 0.2;
      return [...titleSfx('step3'), { t: S('step3').start + 0.4, name: 'pop', vol: 0.35 },
        { t: wt('a_s3a', 'paste') - 0.1, name: 'pop', vol: 0.5 },
        ...every(tAsk, a.end - 0.1, 0.09, 0.5, 7).map((s) => ({ t: s, name: 'type', vol: 0.28 })),
        { t: a.end - 0.5, name: 'boop', vol: 0.5 },
        ...every(tCode, wt('a_s3b', 'draws'), 0.08, 0.5, 8).map((s) => ({ t: s, name: 'type', vol: 0.18 })),
        { t: wt('a_s3b', 'draws') - 0.1, name: 'pop', vol: 0.5 }, { t: wt('a_s3b', 'music') - 0.15, name: 'sparkle', vol: 0.35 },
        { t: tTog, name: 'whoosh', vol: 0.4 }, { t: tTog + 0.75, name: 'ding', vol: 0.6 },
        { t: c.start, name: 'pop', vol: 0.4 }, { t: wt('a_s3c', 'runs') - 0.2, name: 'swoop', vol: 0.5 },
        { t: d.start, name: 'pop', vol: 0.4 }, { t: wt('a_s3d', 'handles') - 0.3, name: 'tick', vol: 0.4 }];
    },
  };

  // ---------------------------------------------------------------- 7. STEP 4
  const FIXMSG = 'fix her arm, make her smile, softer music';
  const PX = 340, PY = 360, PW = 400, PH = 711;
  function step4Times() {
    const r = L('r_s4a'), a = L('a_s4a');
    return { typeA: r.end + 0.4, typeB: r.end + 2.2, send: r.end + 2.45, fix: a.start - 0.2 };
  }
  function step4Visual(ctx, t) {
    const r = L('r_s4a'), a = L('a_s4a'), b = L('a_s4b'), c = L('a_s4c');
    const T4 = step4Times();
    const win = pop(t, S('step4').start + 0.4, 0.5);
    let ver = t < T4.fix ? 1 : 2;
    if (t > b.start) ver = Math.min(5, 3 + Math.floor((t - b.start) / 1.0));
    if (t > wt('a_s4c', 'next version') - 0.2) ver = 6;
    zoomAt(ctx, 540, 715, win, () => {
      // older versions stacked behind
      const ghosts = Math.min(4, ver - 1);
      for (let i = ghosts; i >= 1; i--) fillRR(ctx, PX - i * 16, PY - i * 16, PW, PH, 34, mix('#d9cbb5', '#efe4d2', i / 4));
      fillRR(ctx, PX - 12, PY - 12, PW + 24, PH + 24, 40, '#2d2a3e');
      const kitchenAt = (fixed) => {
        ctx.save(); rrect(ctx, PX, PY, PW, PH, 28); ctx.clip(); ctx.translate(PX, PY); ctx.scale(PW / W, PH / H);
        const g = fixed ? { smile: 0.65, squint: 0.35, lids: 0.75, browTilt: 0 }
          : { smile: -0.35, browTilt: -0.5, lids: 0.8, armOffset: [40 + Math.sin(t * 2) * 12, -175 + Math.sin(t * 3) * 22] };
        P.kitchen(ctx, t, { grandma: g });
        ctx.restore();
      };
      const wipe = ease.inOut(prog(t, T4.fix, T4.fix + 0.4));
      if (wipe < 1) kitchenAt(false);
      if (wipe > 0) { ctx.save(); ctx.beginPath(); ctx.rect(PX, PY, PW, PH * wipe); ctx.clip(); kitchenAt(true); ctx.restore(); if (wipe < 1) fillRR(ctx, PX, PY + PH * wipe - 4, PW, 8, 4, '#ffffff'); }
      // version badge + progress bar
      fillRR(ctx, PX + 20, PY + 20, 96, 52, 26, '#2d2a3e'); text(ctx, 'v' + ver, PX + 68, PY + 47, { size: 32, weight: 900, color: '#ffd166' });
      fillRR(ctx, PX + 24, PY + PH - 26, PW - 48, 8, 4, 'rgba(255,255,255,0.45)'); fillRR(ctx, PX + 24, PY + PH - 26, (PW - 48) * ((t * 0.08) % 1), 8, 4, '#ff8f6b');
      // music meter
      const loud = t < T4.fix ? 1 : 0.45;
      const shake = t > wt('r_s4a', 'music') - 0.2 && t < T4.fix ? Math.sin(t * 50) * 4 : 0;
      for (let i = 0; i < 9; i++) {
        const lit = (i / 9) < loud * (0.85 + 0.15 * Math.abs(noise(t * 5, 3)));
        fillRR(ctx, 790 + shake, 880 - i * 44, 56, 34, 8, lit ? (i > 5 ? '#ff5e57' : i > 3 ? '#ffc04d' : '#5cc98a') : 'rgba(45,42,62,0.15)');
      }
      P.note(ctx, 796 + shake, 480, 0.8, loud > 0.5 ? '#ff5e57' : '#5cc98a');
      // glitch callout
      const gl = U.window(t, wt('r_s4a', 'floating') - 0.2, T4.fix, 0.2);
      if (gl > 0) withAlpha(ctx, gl, () => {
        ctx.save(); ctx.setLineDash([14, 10]); ctx.lineDashOffset = -t * 40;
        ctx.beginPath(); ctx.arc(PX + 302, PY + 400 + Math.sin(t * 3) * 8, 70, 0, TAU); ctx.strokeStyle = '#ff5e57'; ctx.lineWidth = 7; ctx.stroke(); ctx.restore();
      });
      // chat message with the fixes
      const ck = U.window(t, T4.typeA - 0.3, T4.send + 0.3, 0.25);
      if (ck > 0) {
        const fly = ease.in(prog(t, T4.send, T4.send + 0.3));
        withAlpha(ctx, ck, () => {
          fillRR(ctx, 130, 990 - fly * 300, 820, 86, 43, '#ffffff');
          text(ctx, reveal(FIXMSG, t, T4.typeA, T4.typeB), 170, 1033 - fly * 300, { size: 34, weight: 750, color: '#3b3355', align: 'left' });
          circle(ctx, 900, 1033 - fly * 300, 30, '#8f7cf7');
          ctx.beginPath(); ctx.moveTo(888, 1020 - fly * 300); ctx.lineTo(914, 1033 - fly * 300); ctx.lineTo(888, 1046 - fly * 300); ctx.closePath(); ctx.fillStyle = '#fff'; ctx.fill();
        });
      }
      if (t > T4.send && t < T4.fix + 0.3) C.drawBot(ctx, 540, 715, 0.7 * U.window(t, T4.send, T4.fix + 0.3, 0.2), t, { working: true, look: [0, 0.5] });
      // checklist of fixes
      const cl = 1 - prog(t, b.start - 0.3, b.start);
      ['arm fixed', 'smiling', 'music softer'].forEach((s, i) => {
        const k = pop(t, a.start + 0.2 + i * 0.4);
        if (k > 0 && cl > 0) withAlpha(ctx, cl, () => { P.check(ctx, 92, 520 + i * 120, 0.62, k); label(ctx, s, 136 + 80, 522 + i * 120, k, 40, '#3b3355'); });
      });
      // watch -> tweak -> repeat loop
      const lp = U.window(t, b.start - 0.2, L('r_s4b').start + 0.2, 0.3);
      if (lp > 0) withAlpha(ctx, lp, () => {
        ctx.save(); ctx.translate(540, 715);
        for (let i = 0; i < 3; i++) {
          const a0 = t * 1.6 + i * TAU / 3;
          ctx.beginPath(); ctx.ellipse(0, 0, 330, 440, 0, a0, a0 + 1.5); ctx.strokeStyle = '#ff8f6b'; ctx.lineWidth = 14; ctx.lineCap = 'round'; ctx.stroke();
          const ax = Math.cos(a0 + 1.5) * 330, ay = Math.sin(a0 + 1.5) * 440, ang = Math.atan2(Math.cos(a0 + 1.5) * 440, -Math.sin(a0 + 1.5) * 330);
          ctx.save(); ctx.translate(ax, ay); ctx.rotate(ang); ctx.beginPath(); ctx.moveTo(18, 0); ctx.lineTo(-12, -18); ctx.lineTo(-12, 18); ctx.closePath(); ctx.fillStyle = '#ff8f6b'; ctx.fill(); ctx.restore();
        }
        ctx.restore();
        [['watch', 'Watch', 170, 470], ['tweak', 'Tweak', 910, 470], ['repeat', 'Repeat', 910, 960]].forEach(([w, s, x, y]) => {
          const k = pop(t, wt('a_s4b', w) - 0.1);
          if (k > 0) scaled(ctx, x, y, k, () => { fillRR(ctx, -110, -40, 220, 80, 40, '#2d2a3e'); text(ctx, s, 0, 2, { size: 42, weight: 700, family: U.FONTS.title, color: '#ffd166' }); });
        });
      });
      const nv = pop(t, wt('a_s4c', 'next version') - 0.2);
      if (nv > 0) for (let i = 0; i < 5; i++) P.sparkle(ctx, PX + 68 + Math.cos(i * 1.3) * 70 * nv, PY + 46 + Math.sin(i * 1.3) * 50 * nv, 14, rgba('#ffc94d', 1 - prog(t, wt('a_s4c', 'next version'), wt('a_s4c', 'next version') + 1.2)), t * 4);
    });
  }
  scenes.step4 = {
    draw(ctx, t) {
      const r = L('r_s4a'), a = L('a_s4a'), b = L('a_s4b'), r2 = L('r_s4b'), c = L('a_s4c');
      const T4 = step4Times();
      stepFrame(ctx, t, 'step4', 4, 'Watch, tweak, repeat', step4Visual,
        [[0, { gx: 0.4, gy: -0.5, lids: 0.9, smile: 0.1, arms: 'down' }],
          [r.start - 0.3, { arms: 'point', squint: 0.25, browTilt: -0.2, smile: -0.1, gx: 0.6, gy: -0.6 }],
          [T4.typeA - 0.3, { arms: 'phone', typing: true, gy: 0.75, gx: 0, squint: 0, browTilt: 0 }],
          [T4.send, { arms: 'down', typing: false, gx: 0.4, gy: -0.5 }],
          [T4.fix + 0.3, { brow: 0.45, smile: 0.45 }],
          [r2.start - 0.4, { browTilt: 0.65, smile: -0.25, brow: 0.0, gx: 0.9, gy: 0.05 }],
          [c.start + 1.0, { browTilt: 0.15, smile: 0.35, gx: 0.4, gy: -0.5 }],
          [c.end - 0.4, { smile: 0.55, squint: 0.2 }]],
        [[0, { gx: -0.4, gy: -0.5, smile: 0.3, arms: 'down' }],
          [r.start, { gx: -1, gy: 0, smile: 0.4 }],
          [a.start, { arms: 'palm', gx: -0.4, gy: -0.6, smile: 0.45 }],
          [b.start, { arms: 'down' }],
          [r2.start, { gx: -1, gy: 0, browTilt: 0.2 }],
          [c.start, { arms: 'palm', smile: 0.55, browTilt: 0 }],
          [c.end, { arms: 'down' }]]);
    },
    sfx() {
      const a = L('a_s4a'), b = L('a_s4b'), T4 = step4Times();
      return [...titleSfx('step4'), { t: S('step4').start + 0.4, name: 'pop', vol: 0.35 },
        { t: wt('r_s4a', 'floating') - 0.2, name: 'glitch', vol: 0.45 },
        ...every(T4.typeA, T4.typeB, 0.1, 0.6, 11).map((s) => ({ t: s, name: 'type', vol: 0.3 })),
        { t: T4.send, name: 'send', vol: 0.55 }, { t: T4.fix, name: 'swoop', vol: 0.45 }, { t: T4.fix + 0.4, name: 'ding', vol: 0.5 },
        ...[0, 1, 2].map((i) => ({ t: a.start + 0.2 + i * 0.4, name: 'pop', vol: 0.35 })),
        ...['watch', 'tweak', 'repeat'].map((w) => ({ t: wt('a_s4b', w) - 0.1, name: 'pop', vol: 0.45 })),
        { t: wt('a_s4c', 'next version') - 0.2, name: 'sparkle', vol: 0.45 }];
    },
  };

  // ---------------------------------------------------------------- 8. PAYOFF
  function lumpy(ctx, x, y, s, t) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    ctx.beginPath();
    for (let i = 0; i <= 24; i++) { const a = Math.PI + i / 24 * Math.PI, r = 44 + noise(i * 0.9, 7) * 10; ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r * 0.75 + 10); }
    ctx.closePath(); ctx.fillStyle = '#f2e6d0'; ctx.fill(); ctx.strokeStyle = '#d6c3a3'; ctx.lineWidth = 3; ctx.stroke();
    circle(ctx, 14, -6, 9, '#c98b6b');
    ctx.restore();
  }
  function kitchenFull(ctx, t) {
    const sc = S('payoff'), g = L('g_tuck');
    const laugh = U.window(t, sc.start + 0.4, g.start - 0.4, 0.3);
    const tg = talk('grandma', t);
    const gf = face(t, [
      [0, { smile: 0.85, squint: 0.6, lids: 0.45, gx: -0.7, gy: 0.4, tilt: 0.07 }],
      [g.start - 0.4, { smile: 0.5, squint: 0.3, lids: 0.6, gx: -0.2, gy: 0.9, tilt: 0.09 }],
      [g.end + 0.2, { smile: 0.75, squint: 0.45, gx: -0.7, gy: 0.4, lids: 0.6 }],
    ]);
    const kf = face(t, [
      [0, { smile: 0.15, gx: 0.2, gy: 0.6, lids: 0.95, browTilt: 0.3 }],
      [sc.start + 0.9, { smile: 0.45, gx: 0.8, gy: -0.6, browTilt: 0, brow: 0.3 }],
      [g.start, { gx: 0.5, gy: 0.4, smile: 0.3, mouthO: 0.15 }],
      [g.end + 0.2, { gx: 0.8, gy: -0.6, smile: 0.8, squint: 0.4, mouthO: 0 }],
    ]);
    const fold = ease.inOut(prog(t, g.start + 0.3, g.end - 0.2));
    P.kitchen(ctx, t, {
      grandma: Object.assign({}, gf, { open: laugh > 0 ? 0.18 + 0.22 * Math.abs(Math.sin(t * 8)) * laugh : tg.open, width: tg.width, tilt: gf.tilt + Math.sin(t * 8) * 0.012 * laugh }),
      kid: Object.assign({}, kf, { arms: 'counterHigh' }),
      extra: (c) => { P.dumpling(c, 660, 1232, 0.95, fold); lumpy(c, 300, 1240, 0.75, t); },
    });
    // "now playing" chip
    fillRR(ctx, 290, 222, 500, 76, 38, 'rgba(30,27,46,0.72)');
    ctx.beginPath(); ctx.moveTo(332, 242); ctx.lineTo(332, 278); ctx.lineTo(362, 260); ctx.closePath(); ctx.fillStyle = '#ffd166'; ctx.fill();
    text(ctx, 'dumpling_lesson.mp4', 560, 261, { size: 30, weight: 800, color: '#fff', family: U.FONTS.mono });
  }
  function rileyCloseup(ctx, t) {
    const r = L('r_her');
    ctx.save();
    camera(ctx, 2.15, 540, 990, 540, 905);
    P.nightRoom(ctx, t, { clockMin: 58 });
    const f = face(t, [
      [0, { lids: 0.8, gy: 0.62, gx: 0, brow: 0.3, browTilt: 0.5, smile: 0.12, shine: 0.6 }],
      [r.start - 1.5, { shine: 1, smile: 0.26 }, 1.0],
      [r.end + 0.4, { lids: 0.32, smile: 0.4, squint: 0.2, gy: 0.4 }, 1.2],
    ]);
    f.smile += Math.sin(t * 7) * 0.03;
    riley(ctx, t, 540, 1010, 1, f, { arms: 'phone', phoneScreen: '#ffd9a0', tear: prog(t, r.start - 1.2, r.start + 2.6) });
    P.couchFront(ctx);
    P.phoneGlow(ctx, 540, 1300, 1.3, '#ffc27a', 700);
    ctx.restore();
    P.vignette(ctx, 0.6);
  }
  let offPay = null;
  scenes.payoff = {
    draw(ctx, t) {
      const g = L('g_tuck');
      const cut = ease.inOut(prog(t, g.end + 0.9, g.end + 1.9));
      if (cut < 1) kitchenFull(ctx, t);
      if (cut > 0) {
        if (cut >= 1) { rileyCloseup(ctx, t); return; }
        offPay = offPay || X.makeCanvas();
        const o = offPay.ctx; o.setTransform(X.scale, 0, 0, X.scale, 0, 0);
        rileyCloseup(o, t);
        ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = cut; ctx.drawImage(offPay.c, 0, 0); ctx.restore();
      }
    },
    sfx() { return [{ t: S('payoff').start + 0.2, name: 'musicbox', vol: 0.0 }]; },
  };

  // ---------------------------------------------------------------- 9. STYLES + meta reveal
  function stylesGrid(ctx, t) {
    const a = L('a_st1'), b = L('a_st2');
    ctx.fillStyle = vgrad(ctx, 0, H, ['#efe9ff', '#fff2e3']); ctx.fillRect(0, 0, W, H);
    P.stepTitle(ctx, '+', 'Not just one style', t, S('styles').start + 0.25);
    const intro = U.window(t, a.start - 0.2, wt('a_st1', 'pixel') - 0.1, 0.25);
    if (intro > 0) label(ctx, 'not just this style...', 540, 700, intro, 64, '#5b4a7a');
    const tiles = [
      [wt('a_st1', 'pixel') - 0.15, 90, 380, 'pixel art', (x, y, w, h) => { ctx.fillStyle = '#2d2a3e'; ctx.fillRect(x, y, w, h); P.pixelSprite(ctx, x + w / 2 - 110, y + 30 + Math.round(Math.sin(t * 3)) * 6, 22, t); }],
      [wt('a_st1', 'paper') - 0.15, 560, 380, 'paper cut-outs', (x, y, w, h) => P.paperScene(ctx, x, y, w, h, t)],
      [wt('a_st1', '3D') - 0.15, 90, 760, '3D', (x, y, w, h) => { ctx.fillStyle = '#1e1b2e'; ctx.fillRect(x, y, w, h); P.cube3d(ctx, x + w / 2, y + h / 2, 82, t); }],
      [wt('a_st1', 'possible') - 0.3, 560, 760, '...what else?', (x, y, w, h) => { ctx.fillStyle = '#ffe9c7'; ctx.fillRect(x, y, w, h); text(ctx, '?', x + w / 2, y + h / 2 + Math.sin(t * 3) * 10, { size: 190, weight: 700, family: U.FONTS.title, color: '#ff8f6b' }); for (let i = 0; i < 4; i++) P.sparkle(ctx, x + 70 + i * 90, y + 50 + (i % 2) * 190, 16 + 6 * Math.sin(t * 4 + i), '#ffc94d', t * 2); }],
    ];
    tiles.forEach(([t0, x, y, lb, draw]) => {
      const k = pop(t, t0);
      if (k <= 0) return;
      scaled(ctx, x + 215, y + 175, k, () => {
        ctx.translate(-215, -175);
        ctx.fillStyle = 'rgba(60,40,90,0.12)'; rrect(ctx, 6, 10, 430, 350, 28); ctx.fill();
        ctx.save(); rrect(ctx, 0, 0, 430, 350, 28); ctx.clip(); draw(0, 0, 430, 290); fillRR(ctx, 0, 290, 430, 60, 0, '#ffffff'); ctx.restore();
        label(ctx, lb, 215, 320, 1, 42, '#3b3355');
      });
    });
    cast(ctx, t,
      [[0, { gx: 0.3, gy: -0.6, smile: 0.2, brow: 0.3, lids: 0.95 }], [wt('a_st1', '3D'), { brow: 0.6, smile: 0.45, mouthO: 0.35 }, 0.3], [wt('a_st1', '3D') + 0.8, { mouthO: 0, smile: 0.5 }], [b.start, { gx: 0.9, gy: 0 }]],
      [[0, { gx: -0.4, gy: -0.6, smile: 0.4, arms: 'down' }], [a.start + 0.3, { arms: 'palm' }], [a.end - 0.5, { arms: 'down', gx: -1, gy: 0 }], [b.start, { smile: 0.6, squint: 0.3, arms: 'point', gx: -0.3, gy: -0.5 }]]);
  }
  function composeMeta(ctx, src, t, k, typedFrom) {
    ctx.fillStyle = '#1e1b2e'; ctx.fillRect(0, 0, W, H);
    for (let i = 0; i < 9; i++) circle(ctx, hash(i * 3) * W, hash(i * 7) * H, 120 + hash(i) * 120, rgba('#2b2640', 0.8));
    const s = lerp(1, 0.52, k), cx = 540, cy = lerp(960, 925, k);
    // terminal chrome around the shrunken frame
    withAlpha(ctx, prog(k, 0.3, 0.8), () => {
      fillRR(ctx, 60, 200, 960, 1220, 34, '#2b2640');
      ['#ff6b6b', '#ffd166', '#06d6a0'].forEach((c, i) => circle(ctx, 105 + i * 36, 244, 12, c));
      text(ctx, '>', 100, 312, { size: 32, color: '#06d6a0', family: U.FONTS.mono, align: 'left', weight: 700 });
      text(ctx, reveal('make a video about how I make videos', t, typedFrom, typedFrom + 1.4), 136, 312, { size: 30, color: '#e8e4ff', family: U.FONTS.mono, align: 'left', weight: 500 });
      const done = pop(t, typedFrom + 1.6);
      if (done > 0) { P.check(ctx, 128, 372, 0.55, done); text(ctx, 'this_video.mp4', 166, 374, { size: 30, color: '#ffd166', family: U.FONTS.mono, align: 'left', weight: 700, alpha: done }); }
    });
    ctx.save(); ctx.translate(cx, cy); ctx.scale(s, s);
    fillRR(ctx, -W / 2 - 22, -H / 2 - 22, W + 44, H + 44, 70, '#0b0c12');
    rrect(ctx, -W / 2, -H / 2, W, H, 52); ctx.clip();
    ctx.drawImage(src, -W / 2, -H / 2, W, H);
    ctx.restore();
    const bk = pop(t, typedFrom + 0.6);
    if (bk > 0) C.drawBot(ctx, 925, 1180, 0.8 * bk, t, { wave: true, happy: true });
  }
  let offA = null, offB = null;
  scenes.styles = {
    draw(ctx, t) {
      const tThis = wt('a_st2', 'this video');
      const k1 = ease.inOut(prog(t, tThis - 0.3, tThis + 1.1));
      const k2 = ease.inOut(prog(t, tThis + 2.3, tThis + 3.6));
      if (k1 <= 0) { stylesGrid(ctx, t); return; }
      offA = offA || X.makeCanvas(); offB = offB || X.makeCanvas();
      const sc = X.scale;
      offA.ctx.setTransform(sc, 0, 0, sc, 0, 0); stylesGrid(offA.ctx, t);
      if (k2 <= 0) { composeMeta(ctx, offA.c, t, k1, tThis); return; }
      offB.ctx.setTransform(sc, 0, 0, sc, 0, 0); composeMeta(offB.ctx, offA.c, t, 1, tThis);
      composeMeta(ctx, offB.c, t, k2, tThis + 2.3);
    },
    sfx() {
      const tThis = wt('a_st2', 'this video');
      return [...titleSfx('styles'), ...['pixel', 'paper', '3D', 'possible'].map((w) => ({ t: wt('a_st1', w) - 0.15, name: 'pop', vol: 0.45 })),
        { t: tThis - 0.3, name: 'zoomout', vol: 0.55 }, { t: tThis + 2.3, name: 'zoomout', vol: 0.45 },
        ...every(tThis, tThis + 1.4, 0.08, 0.5, 13).map((s) => ({ t: s, name: 'type', vol: 0.2 })),
        { t: tThis + 1.6, name: 'ding', vol: 0.5 }];
    },
  };

  // ---------------------------------------------------------------- 10. CLOSE + end card
  function closeRoom(ctx, t) {
    const sc = S('close'), c1 = L('a_c1'), c1b = L('a_c1b'), c2 = L('a_c2'), r = L('r_c');
    ctx.save();
    camera(ctx, lerp(1.0, 1.1, prog(t, sc.start, r.end)), 540, 960, 540, 960);
    P.nightRoom(ctx, t, { lamp: 1, rain: 0.5, clockMin: 3 });
    const typing = t > c1.start + 0.5 && t < c2.start - 0.2;
    const f = face(t, [
      [0, { lids: 0.85, gy: 0.75, gx: 0, smile: 0.3, brow: 0.2 }],
      [c1b.start, { smile: 0.35, gy: 0.7 }],
      [wt('a_c1b', 'twenty') - 0.2, { gx: 0.7, gy: -0.75, smile: 0.25 }],
      [wt('a_c1b', 'enough') - 0.2, { gx: 0, gy: -0.85, smile: 0.4 }],
      [c2.start, { gy: -0.2, gx: 0, smile: 0.5, lids: 0.95, brow: 0.35 }],
      [r.start - 0.3, { smile: 0.6, brow: 0.45, squint: 0.15, gy: 0.1 }],
      [r.end + 0.2, { gy: 0.75, smile: 0.55 }],
    ]);
    riley(ctx, t, 540, 1010, 1, f, { arms: 'phone', typing: typing || (t > r.end && t < r.end + 1.2), phoneScreen: '#fff1d6' });
    P.couchFront(ctx, { blanket: '#d4775f' });
    P.phoneGlow(ctx, 540, 1300, 0.8, '#ffe0a8');
    P.lampLight(ctx, 1);
    // the 20-minute timer on the wall clock
    const tm = U.window(t, wt('a_c1b', 'twenty') - 0.3, c1b.end + 0.3, 0.3);
    if (tm > 0) withAlpha(ctx, tm, () => {
      ctx.beginPath(); ctx.moveTo(840, 430); ctx.arc(840, 430, 64, -Math.PI / 2, -Math.PI / 2 + TAU / 3 * prog(t, wt('a_c1b', 'twenty') - 0.3, wt('a_c1b', 'twenty') + 1.0)); ctx.closePath();
      ctx.fillStyle = rgba('#ffd166', 0.6); ctx.fill();
      fillRR(ctx, 760, 520, 160, 60, 30, '#ffd166'); text(ctx, '20 min', 840, 551, { size: 34, weight: 900, color: '#2d2a3e' });
    });
    ctx.restore();
    // thought bubble: spark + memory, then one scene moving forward
    const tb = pop(t, c1.start + 0.3, 0.6);
    if (tb > 0) {
      P.thought(ctx, 450, 590, 580, 360, tb, [520, 830]);
      scaled(ctx, 450, 590, tb, () => {
        P.lightbulb(ctx, -150, 0, 0.55, anim(t, wt('a_c1', 'spark') - 0.1, 0.3), t);
        P.polaroid(ctx, 110, -10, 0.55, t, 0.06);
        const fs = U.window(t, wt('a_c1b', 'one scene') - 0.4, c2.start + 0.2, 0.3);
        if (fs > 0) withAlpha(ctx, fs, () => {
          fillRR(ctx, -280, -175, 560, 350, 150, '#ffffff');
          P.filmStrip(ctx, -250, -50, 500, 100, ['#e8e2d6', '#e8e2d6', '#e8e2d6', '#e8e2d6', '#e8e2d6'], t);
          const lit = Math.min(4, Math.floor(prog(t, wt('a_c1b', 'one scene'), wt('a_c1b', 'one scene') + 0.9) * 2));
          for (let i = 0; i <= lit; i++) fillRR(ctx, -240 + i * 96 + 6, -20, 84, 40, 8, ['#ffd3a1', '#f6d9a5', '#bfe3f2'][i % 3]);
          label(ctx, '+1 scene', 0, 110, 1, 48, '#c4553f');
        });
      });
      const w1 = pop(t, wt('a_c1', 'spark') - 0.1), w2 = pop(t, wt('a_c1', 'honest') - 0.2);
      const wf = 1 - prog(t, c1b.start - 0.2, c1b.start + 0.2);
      if (w1 > 0 && wf > 0) withAlpha(ctx, wf, () => scaled(ctx, 290, 300, w1, () => { fillRR(ctx, -140, -44, 280, 88, 44, '#ffd166'); text(ctx, 'a spark', 0, 2, { size: 46, family: U.FONTS.hand, weight: 400, color: '#2d2a3e' }); }));
      if (w2 > 0 && wf > 0) withAlpha(ctx, wf, () => scaled(ctx, 700, 300, w2, () => { fillRR(ctx, -210, -44, 420, 88, 44, '#ffffff'); text(ctx, '+ a few honest words', 0, 2, { size: 44, family: U.FONTS.hand, weight: 400, color: '#2d2a3e' }); }));
      const tap = r.end + 0.15, burst = prog(t, tap, tap + 0.9);
      if (burst > 0 && burst < 1) for (let i = 0; i < 10; i++) { const a = i / 10 * TAU; P.sparkle(ctx, 540 + Math.cos(a) * 260 * ease.out(burst), 1310 + Math.sin(a) * 200 * ease.out(burst), 20 * (1 - burst), '#ffd166', t * 4); }
    }
    P.vignette(ctx, 0.35);
  }
  const STEPS = [['1', 'Find a spark', 'a memory, a feeling, a post'], ['2', 'Ramble to a chatbot', 'it shapes a script'], ['3', 'Ask for the video', 'it runs the tools'], ['4', 'Watch, tweak, repeat', 'in plain words']];
  function endCard(ctx, t, t0) {
    ctx.fillStyle = vgrad(ctx, 0, H, ['#fff5e6', '#ffe6c7']); ctx.fillRect(0, 0, W, H);
    P.warmBG(ctx, t, 'rgba(0,0,0,0)');
    const k = pop(t, t0 + 0.2);
    scaled(ctx, 540, 470, k, () => {
      text(ctx, 'Your story is', 0, -50, { size: 84, weight: 700, family: U.FONTS.title, color: '#2d2a3e' });
      text(ctx, 'worth telling.', 0, 50, { size: 84, weight: 700, family: U.FONTS.title, color: '#e2674b' });
    });
    STEPS.forEach(([n, a, b], i) => {
      const kk = pop(t, t0 + 0.8 + i * 0.35);
      if (kk <= 0) return;
      scaled(ctx, 540, 760 + i * 150, kk, () => {
        fillRR(ctx, -400, -62, 800, 124, 62, '#ffffff');
        circle(ctx, -338, 0, 44, '#ffb347');
        text(ctx, n, -338, 3, { size: 50, weight: 700, family: U.FONTS.title, color: '#2d2a3e' });
        text(ctx, a, -268, -16, { size: 44, weight: 800, color: '#2d2a3e', align: 'left' });
        text(ctx, b, -268, 30, { size: 30, weight: 650, color: '#8a7f73', align: 'left' });
      });
    });
    const f = pop(t, t0 + 2.6);
    if (f > 0) scaled(ctx, 540, 1405, f, () => label(ctx, 'made with words + a chatbot', 0, 0, 1, 56, '#6b5b7a'));
    C.drawBot(ctx, 900, 1390, 0.6 * pop(t, t0 + 2.9), t, { happy: true, wave: true });
  }
  let offE = null;
  scenes.close = {
    draw(ctx, t) {
      const r = L('r_c'), t0 = r.end + 1.1;
      const k = ease.inOut(prog(t, t0, t0 + 0.8));
      if (k < 1) closeRoom(ctx, t);
      if (k > 0) {
        if (k >= 1) { endCard(ctx, t, t0); return; }
        offE = offE || X.makeCanvas();
        offE.ctx.setTransform(X.scale, 0, 0, X.scale, 0, 0); endCard(offE.ctx, t, t0);
        ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = k; ctx.drawImage(offE.c, 0, 0); ctx.restore();
      }
    },
    sfx() {
      const c1 = L('a_c1'), r = L('r_c'), t0 = r.end + 1.1;
      return [{ t: c1.start + 0.3, name: 'sparkle', vol: 0.4 }, { t: wt('a_c1', 'spark') - 0.1, name: 'pop', vol: 0.4 }, { t: wt('a_c1', 'honest') - 0.2, name: 'pop', vol: 0.4 },
        { t: wt('a_c1b', 'twenty') - 0.3, name: 'tick', vol: 0.45 }, { t: wt('a_c1b', 'one scene') - 0.4, name: 'pop', vol: 0.4 },
        { t: r.end + 0.15, name: 'spark', vol: 0.6 }, { t: t0, name: 'whoosh', vol: 0.35 },
        ...[0, 1, 2, 3].map((i) => ({ t: t0 + 0.8 + i * 0.35, name: 'pop', vol: 0.35 })), { t: t0 + 2.6, name: 'ding', vol: 0.4 }];
    },
  };

  return scenes;
};
