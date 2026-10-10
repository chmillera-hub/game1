// Scene choreography. Every scene is a pure function of global time t.
const L = require('./lib');
const C = require('./chars');
const B = require('./bg');
const P = require('./props');
const { W, H, clamp, lerp, smooth, easeOut, easeIn, easeInOut, easeOutBack, prog, pulse, ellipse, fillStroke } = L;

const M = n => L.mark(n);
const LS = id => L.lineStart(id);
const LE = id => L.lineEnd(id);
const during = (t, id, pre = 0, post = 0) => t >= LS(id) - pre && t < LE(id) + post;
const SC = Object.fromEntries(L.TL.scenes.map(s => [s.name, s]));

const BLUE = '#2F6BFF';
const NAILS_BLUE = [BLUE, BLUE, BLUE, BLUE, BLUE];
const ONES = [1, 1, 1, 1, 1];

function easeOutBounce(x) {
  x = clamp(x); const n1 = 7.5625, d1 = 2.75;
  if (x < 1 / d1) return n1 * x * x;
  if (x < 2 / d1) return n1 * (x -= 1.5 / d1) * x + 0.75;
  if (x < 2.5 / d1) return n1 * (x -= 2.25 / d1) * x + 0.9375;
  return n1 * (x -= 2.625 / d1) * x + 0.984375;
}
function lookAt(x0, y0, x1, y1, k = 1) {
  const dx = x1 - x0, dy = y1 - y0, d = Math.hypot(dx, dy) || 1;
  const m = Math.min(1, d / 160) * k;
  return [dx / d * m, dy / d * m];
}

// ---- character helpers with auto blink + lip-sync -----------------------
function aceE(t, e = {}) {
  const a = L.amp('ACE', t);
  return { smile: 0.6, ...e, open: Math.max(e.open || 0, a * 0.95), blink: e.closed ? 0 : L.blink('ACE', t) };
}
// the floor is drawn in front of Ace's body (she sits behind the pink blanket / rug)
let pendingFloor = null;
function room(ctx, t, kind, hz) {
  if (kind === 'star') { B.starWall(ctx, t, hz); pendingFloor = () => B.pinkFloor(ctx, t, hz); }
  else { B.orangeRoom(ctx, t, hz, 'wall'); pendingFloor = () => B.orangeRoom(ctx, t, hz, 'floor'); }
}
function drawAce(ctx, x, y, s, e, t, o = {}) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  if (o.body !== false) C.aceBody(ctx, o.shirt);
  C.aceHead(ctx, aceE(t, e), t);
  ctx.restore();
  if (pendingFloor) { const f = pendingFloor; pendingFloor = null; f(); }
}
function bbE(t, e = {}) {
  const a = L.amp('BB', t);
  return { ...e, t, open: Math.max(e.open || 0, a), blink: L.blink('BB', t) };
}
function drawBall(ctx, x, y, R, ang, e, t) {
  ctx.save(); ctx.translate(x, y);
  C.hamsterInBall(ctx, { R, ang, e: bbE(t, e) });
  ctx.restore();
}
function drawHamster(ctx, x, y, s, e, t) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  C.hamster(ctx, bbE(t, e));
  ctx.restore();
}
function drawHand(ctx, x, y, s, rot, o, t) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot || 0); ctx.scale(s, s);
  C.hand(ctx, { t, ...o });
  ctx.restore();
}
function shadow(ctx, x, y, w) {
  ellipse(ctx, x, y, w, w * 0.16); ctx.fillStyle = 'rgba(120,40,90,0.18)'; ctx.fill();
}

// =========================================================== TITLE =====
function title(ctx, t) {
  const lt = t - SC.title.start;
  B.titleBg(ctx, lt);
  // Ace pops in
  const ap = easeOutBack(prog(lt, 0.15, 0.7));
  if (ap > 0) {
    const look = lt < 2.4 ? [0.7, 0.1] : lt < 4.6 ? [0.5, 0.7] : [0, 0.15];
    drawAce(ctx, 215, 330, 1.02 * ap, { look, smile: 0.85, wink: pulse(lt, 5.4, 0.7) > 0.25 ? 1 : 0, blush: 0.3 }, t, { body: false });
  }
  // title words drop in
  const word = (txt, x, y, size, t0, col) => {
    const p = prog(lt, t0, 0.8);
    if (p <= 0) return;
    const yy = y - (1 - easeOutBounce(p)) * 520;
    ctx.save(); ctx.translate(x, yy); ctx.rotate(Math.sin(lt * 1.6 + x) * 0.02);
    ctx.font = `${size}px "Luckiest Guy"`; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    ctx.lineJoin = 'round';
    ctx.fillStyle = 'rgba(30,40,120,0.25)'; ctx.fillText(txt, 6, 8);
    ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 14; ctx.strokeText(txt, 0, 0);
    ctx.fillStyle = col; ctx.fillText(txt, 0, 0);
    ctx.restore();
  };
  word('ACE', 530, 330, 150, 0.7, '#2459D8');
  word('AND', 535, 480, 120, 1.15, '#2F6BE8');
  word('BLUEBERRY', 360, 680, 104, 1.6, '#2459D8');
  // Blueberry hops in from the right
  const hp = prog(lt, 2.1, 0.8);
  if (hp > 0) {
    const x = lerp(820, 520, easeOut(hp)), y = 905 - Math.sin(hp * Math.PI) * 140 - (lt > 3 ? Math.abs(Math.sin((lt - 3) * 4)) * 18 * (lt < 4.2 ? 1 : 0) : 0);
    shadow(ctx, x, 985, 70);
    drawHamster(ctx, x, y, 1.6, { pose: lt > 3.0 ? 'wave' : 'rest', happy: during(t, 'N_title', 0, 0.5) ? 1 : 0, look: [-0.4, -0.3], squash: hp < 1 ? 0 : pulse(lt, 2.9, 0.25) }, t);
  }
}

// =========================================================== HELLO =====
const TWO = { ax: 290, ay: 340, as: 1.25, bx: 515, by: 790, R: 118, hz: 640 };
function hello(ctx, t) {
  room(ctx, t, 'star', TWO.hz);
  const tb = t - M('hello.ballIn');
  let bx = lerp(900, TWO.bx, easeOut(prog(tb, 0, 2.0)));
  let by = TWO.by;
  const moving = tb > 0 && tb < 1.8;
  // play: wiggle + hop
  const ts = t - M('hello.spin');
  if (ts > 0) bx += Math.sin(ts * 5) * 26 * window(ts, 0, 0.3, 2.0, 0.4);
  const hop = during(t, 'BB_whee', 0.1, 0.4) ? Math.sin(clamp((t - LS('BB_whee') + 0.1) / 0.75) * Math.PI) * 90 : 0;
  by -= hop;
  const ang = (bx - TWO.bx) / TWO.R;
  // Ace
  const lookBall = lookAt(TWO.ax, TWO.ay, bx, by);
  const hi = during(t, 'ACE_hi', 0.2, 0.3);
  const play = t > LS('N_play1');
  drawAce(ctx, TWO.ax, TWO.ay, TWO.as, {
    look: tb < 0 ? [Math.sin(t * 1.3) * 0.5, 0.1] : lookBall,
    smile: 0.75, brow: hi ? { raise: 0.6 } : undefined, blush: play ? 0.5 : 0.1,
    squint: during(t, 'BB_whee', 0, 0.8) ? 1 : 0, wide: moving ? 0.5 : 0, hairBounce: hop * 0.05,
  }, t);
  // Ace waves
  const wv = window(t, LS('ACE_hi') - 0.5, 0.3, LE('ACE_hi') + 0.6, 0.4);
  if (wv > 0) drawHand(ctx, 95, 800 - wv * 230, 1.05, -0.15 + Math.sin(t * 9) * 0.25, { arm: 200, sleeve: '#39C3C6', armSleeveY: 70, nails: { state: 'bitten', len: 7 } }, t);
  // Blueberry
  L.ellipse(ctx, bx, TWO.by + TWO.R * 0.96, TWO.R * 0.8 * (1 - hop / 300), 14); ctx.fillStyle = 'rgba(150,50,100,0.16)'; ctx.fill();
  const bbHi = during(t, 'BB_hi', 0.1, 0.4);
  drawBall(ctx, bx, by, TWO.R, ang, {
    run: moving ? 1 : 0, pose: bbHi ? 'wave' : during(t, 'BB_whee', 0.1, 0.6) ? 'up' : 'rest',
    look: moving ? [-1, 0] : [-0.7, -0.6], happy: during(t, 'BB_whee', 0, 0.8) || during(t, 'N_play3') ? 1 : 0,
  }, t);
  // sparkles on the ball during "favorite toy, his purple ball"
  const sh = t - M('hello.shine');
  if (sh > 0 && sh < 3.2) {
    for (let i = 0; i < 6; i++) {
      const a = i * 1.05 + sh * 0.6, p = (sh * 1.4 + i * 0.37) % 1;
      L.sparkle(ctx, bx + Math.cos(a) * TWO.R * 1.08, by + Math.sin(a) * TWO.R * 1.08, 15 * Math.sin(p * Math.PI), '#FFFFFF', window(sh, 0, 0.3, 2.8, 0.4));
    }
  }
  P.heartPop(ctx, (TWO.ax + bx) / 2 + 30, 560, t, LS('N_play1') + 1.6, 36);
}
function window(t, a, din, b, dout) { return L.window_(t, a, din, b, dout); }

// ============================================================ ROLL =====
const RL = { hz: 560, ax: 360, ay: 300, as: 0.95, y: 820, R: 100 };
function rollBallState(t) {
  const z1 = LS('N_fast') + 0.45, z2 = M('roll.fast') + 0.15, z3 = LE('BB_zoom') + 0.35;
  const s0 = LS('N_slow') + 0.1, s1 = LE('BB_slow') + 0.4;
  const v0 = M('roll.visit') + 0.6;
  let x = -300, y = RL.y, R = RL.R, dir = 1, speed = 0;
  const zip = (t0, a, b, d) => { const p = prog(t, t0, d); return { on: p > 0 && p < 1, x: lerp(a, b, easeInOut(p)) }; };
  if (t < s0) {
    for (const [t0, a, b, d] of [[z1, -180, 900, 0.75], [z2, 900, -180, 0.75], [z3, -180, 900, 0.65]]) {
      const z = zip(t0, a, b, d);
      if (z.on) { x = z.x; dir = Math.sign(b - a); speed = 1; }
    }
  } else if (t < v0) {
    x = lerp(-150, 360, easeInOut(prog(t, s0, s1 - s0)));
    speed = t < s1 ? 0.35 : 0;
  } else {
    const p = easeInOut(prog(t, v0, 1.8));
    x = lerp(360, 470, p); y = lerp(RL.y, 700, p); R = lerp(RL.R, 88, p);
    speed = p > 0 && p < 1 ? 0.5 : 0;
  }
  return { x, y, R, dir, speed, ang: x / RL.R + (t >= v0 ? (y - RL.y) / -RL.R * 0.6 : 0) };
}
function roll(ctx, t) {
  room(ctx, t, 'star', RL.hz);
  const b = rollBallState(t);
  const fastPhase = t < LS('N_slow');
  const visitP = prog(t, M('roll.visit') + 2.2, 0.3);
  drawAce(ctx, RL.ax, RL.ay, RL.as, {
    look: [clamp((b.x - RL.ax) / 300, -1, 1), b.x < -100 || b.x > 820 ? 0.4 : 0.85],
    wide: fastPhase && b.speed > 0 ? 0.7 : 0, round: fastPhase && b.speed > 0 ? 0.6 : 0, open: fastPhase && b.speed > 0 ? 0.35 : 0,
    smile: 0.75, squint: visitP > 0 ? 1 : 0, blush: visitP > 0 ? 0.8 : 0.2, brow: fastPhase ? { raise: 0.5 } : undefined,
  }, t);
  P.speedLines(ctx, b.x, b.y, b.dir, b.R, b.speed > 0.9 ? 0.85 : 0);
  ellipse(ctx, b.x, b.y + b.R * 0.97, b.R * 0.75, 12); ctx.fillStyle = 'rgba(150,50,100,0.16)'; ctx.fill();
  const slow = t >= LS('N_slow') && t < M('roll.visit');
  drawBall(ctx, b.x, b.y, b.R, b.ang, {
    run: b.speed > 0 ? (slow ? 0.6 : 1) : 0, look: [b.dir, 0], happy: slow || visitP > 0 ? 1 : 0,
    wide: fastPhase ? 0.4 : 0, pose: visitP > 0 ? 'wave' : (fastPhase && b.speed > 0 ? 'up' : 'rest'),
  }, t);
  P.heartPop(ctx, (RL.ax + b.x) / 2, 520, t, M('roll.visit') + 2.3, 40);
  P.floatingHearts(ctx, 420, 640, t, M('roll.visit') + 2.6, window(t, M('roll.visit') + 2.6, 0.3, SC.roll.end, 0.3), 5, 160);
}

// ============================================================ OOCH =====
function ooch(ctx, t) {
  const sore0 = M('ooch.sore'), why0 = M('ooch.why');
  if (t >= sore0 && t < why0) return soreCloseUp(ctx, t, sore0);
  room(ctx, t, 'star', TWO.hz);
  const push = M('ooch.push'), tap = M('ooch.tap');
  // hand x (wrist)
  let hx = -260, hy = 770;
  const contact = TWO.bx - TWO.R - 175 + 2; // wrist x when fingertip touches ball
  if (t < tap - 0.6) {
    hx = lerp(-260, contact - 70, easeOut(prog(t, push + 0.2, 0.8)));
    hx = lerp(hx, contact + 40, pulse(t, push + 1.3, 0.6));
  } else {
    hx = lerp(contact - 70, contact, easeIn(prog(t, tap - 0.35, 0.35)));
    if (t > tap) hx = lerp(contact, contact - 150, easeOut(prog(t, tap, 0.3)));
    if (t > why0) hx = lerp(contact - 150, -300, easeInOut(prog(t, why0, 0.6)));
  }
  const shake = t > tap ? Math.sin(t * 45) * 10 * (1 - prog(t, tap, 1.2)) : 0;
  // ball pushed
  let bx = TWO.bx;
  bx += 80 * easeOut(prog(t, push + 1.55, 0.9)) * (1 - easeInOut(prog(t, push + 2.7, 1.1)));
  if (t > tap) bx += 12 * pulse(t, tap, 0.4);
  const ang = (bx - TWO.bx) / TWO.R;
  const wince = t > tap + 0.02 && t < tap + 1.3;
  const sad = t > why0;
  drawAce(ctx, TWO.ax, TWO.ay, TWO.as, {
    look: wince ? [0, 0] : sad ? [0.2, 0.6] : lookAt(TWO.ax, TWO.ay, hx + 175, hy - 20),
    wince: wince ? 1 : 0, round: wince ? 0.7 : 0, smile: wince ? -0.3 : sad ? -0.25 : 0.65,
    brow: wince || sad ? { worry: 1 } : undefined, blush: wince ? 0.6 : 0.2, tilt: wince ? Math.sin(t * 30) * 0.02 : 0,
  }, t);
  ellipse(ctx, bx, TWO.by + TWO.R * 0.96, TWO.R * 0.8, 14); ctx.fillStyle = 'rgba(150,50,100,0.16)'; ctx.fill();
  const worried = t > tap + 0.4;
  drawBall(ctx, bx, TWO.by, TWO.R, ang, {
    run: t > push + 1.55 && t < push + 3.8 ? 0.7 : 0, look: worried ? [-0.8, -0.6] : [-1, 0.2],
    worry: worried ? 1 : 0, wide: t > tap && t < tap + 1 ? 0.6 : 0, happy: t > push + 1.6 && t < push + 3.4 ? 1 : 0,
  }, t);
  // pointing hand
  ctx.save(); ctx.translate(hx, hy + shake); ctx.scale(1.35, 1.35); ctx.rotate(-0.12);
  C.pointHand(ctx, { nails: { len: 7, sore: t > tap ? 1 : 0.3 }, bend: t > tap ? 0.3 * (1 - prog(t, tap + 0.5, 0.6)) : 0 });
  ctx.restore();
  // OOCH! burst
  const bp = t - tap;
  if (bp > 0.05 && bp < 1.5) {
    const s = easeOutBack(clamp(bp / 0.25)) * (1 - smooth((bp - 1.2) / 0.3));
    P.burst(ctx, 330, 600, 0.95 * s, 'OOCH!');
  }
}
function soreCloseUp(ctx, t, t0) {
  const g = ctx.createRadialGradient(360, 620, 50, 360, 620, 700);
  g.addColorStop(0, '#FFE3EE'); g.addColorStop(1, '#F7B4CF');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const p = easeOut(prog(t, t0, 0.5));
  const sore = 0.75 + Math.sin(t * 7) * 0.25;
  drawHand(ctx, 370, 1250 + (1 - p) * 400, 3.9, 0, { nails: { state: 'bitten', len: 7, sore }, arm: 300, sleeve: '#39C3C6', armSleeveY: 60 }, t);
  // throb marks around fingertips
  const tips = C.handTips({});
  ctx.strokeStyle = '#FF4F5E'; ctx.lineWidth = 6; ctx.lineCap = 'round';
  tips.forEach((tp, i) => {
    const x = 370 + tp.x * 3.9, y = 1250 + (1 - p) * 400 + tp.y * 3.9;
    const k = (t * 1.6 + i * 0.2) % 1;
    ctx.globalAlpha = Math.sin(k * Math.PI) * p;
    for (const s of [-1, 1]) { ctx.beginPath(); ctx.arc(x, y - 14, 52 + k * 22, s > 0 ? -0.9 : Math.PI - 0.5 + 0.1, s > 0 ? -0.4 : Math.PI + 0.1 - 0.2); ctx.stroke(); }
    ctx.globalAlpha = 1;
  });
}

// ========================================================= BROTHER =====
function twoShotBase(ctx, t, aceExtra = {}, bbExtra = {}, ballDx = 0, ballDy = 0) {
  room(ctx, t, 'star', TWO.hz);
  drawAce(ctx, TWO.ax, TWO.ay, TWO.as, { look: lookAt(TWO.ax, TWO.ay, TWO.bx, TWO.by), ...aceExtra }, t);
  ellipse(ctx, TWO.bx + ballDx, TWO.by + TWO.R * 0.96, TWO.R * 0.8, 14); ctx.fillStyle = 'rgba(150,50,100,0.16)'; ctx.fill();
  drawBall(ctx, TWO.bx + ballDx, TWO.by + ballDy, TWO.R, ballDx / TWO.R, { look: [-0.7, -0.6], ...bbExtra }, t);
}

const BH = { x: 400, y: 890, s: 0.95, rot: 1.2 };
function bedroomScene(ctx, t, o) {
  // o: {morning, gloves, nails, baby: {rise, chomp, mood, green, tilt}, aceE, hand, zzz}
  const morning = o.morning || 0;
  B.bedroom(ctx, t, morning);
  const breath = Math.sin(t * 1.6) * 0.012;
  ctx.save(); ctx.translate(300, 668); ctx.rotate(-0.22); ctx.scale(1.0, 1.0 + breath);
  C.aceHead(ctx, { closed: 1, smile: 0.35, ...(o.aceE || {}), blink: (o.aceE && o.aceE.closed === 0) ? L.blink('ACE', t) : 0 }, t);
  ctx.restore();
  B.blanket(ctx, t, morning, 790);
  // hand resting on the blanket, fingers towards the right edge of the bed
  const h = o.hand || {};
  drawHand(ctx, BH.x + (h.dx || 0), BH.y + (h.dy || 0), BH.s, BH.rot, {
    glove: o.gloves, nails: o.nails, arm: 150, sleeve: '#B9A3F0', armSleeveY: 70, spread: 0.6, hot: h.hot || 0, wiggle: h.wiggle || 0,
  }, t);
  if (o.glovePeel) { // glove sliding off along the fingers
    const gp = o.glovePeel;
    ctx.save(); ctx.globalAlpha = 1 - smooth((gp - 0.6) / 0.4);
    drawHand(ctx, BH.x + Math.sin(BH.rot) * gp * 170, BH.y - Math.cos(BH.rot) * gp * 170, BH.s, BH.rot + gp * 0.3, { glove: true, spread: 0.6 }, t);
    ctx.restore();
  }
  if (o.baby && o.baby.rise > 0) {
    const bb = o.baby;
    const bx = lerp(700, 622, easeOut(bb.rise)), by = lerp(1450, 790, easeOutBack(bb.rise, 1.2));
    ctx.save(); ctx.translate(bx, by);
    // onesie body + little arms
    // onesie: round tummy, collar and snaps
    ctx.beginPath(); ctx.moveTo(-60, 50); ctx.bezierCurveTo(-120, 70, -125, 220, -90, 300);
    ctx.lineTo(90, 300); ctx.bezierCurveTo(125, 220, 120, 70, 60, 50); ctx.closePath();
    fillStroke(ctx, '#9BD7F0', '#5BA9C9', 4);
    ctx.beginPath(); ctx.moveTo(-40, 52); ctx.quadraticCurveTo(0, 80, 40, 52); ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 6; ctx.stroke();
    ctx.fillStyle = '#FFFFFF'; for (const yy of [110, 145, 180]) { ellipse(ctx, 0, yy, 5, 5); ctx.fill(); }
    // little arms reaching up
    for (const s of [-1, 1]) {
      ctx.save(); ctx.translate(s * 78, 90); ctx.rotate(s * 0.35);
      ctx.beginPath(); ctx.roundRect(-15, -80, 30, 95, 15); fillStroke(ctx, '#9BD7F0', '#5BA9C9', 3);
      ellipse(ctx, 0, -84, 17, 17); fillStroke(ctx, '#FFE0CC', '#D69B83', 2.5);
      ctx.restore();
    }
    ctx.scale(0.95, 0.95);
    C.babyHead(ctx, { t, tilt: (bb.tilt || 0.25), mood: bb.mood, chomp: bb.chomp || 0, green: bb.green || 0, look: bb.look || [-0.8, 0.4], blink: L.blink('BABY', t) });
    ctx.restore();
  }
  if (o.zzz) P.zzz(ctx, 420, 560, t, o.zzz);
}

function brother(ctx, t) {
  const flash = M('brother.flash'), flashEnd = M('brother.flashEnd'), hmm = M('brother.hmm');
  if (t >= hmm && t < LE('BB_gloves') + 0.35) return thinking(ctx, t, 'brother');
  // two-shot
  const sheepish = during(t, 'ACE_brother', 0.1, 0.3);
  const giggle = t > M('brother.giggle') && t < LE('ACE_yes') + 0.6;
  const aceGig = during(t, 'ACE_yes', 0.05, 0.5);
  const ok = during(t, 'ACE_ok', 0.2, 0.8);
  twoShotBase(ctx, t, {
    look: sheepish ? [-0.5 + Math.sin(t * 2) * 0.2, 0.5] : undefined,
    brow: sheepish ? { worry: 0.6 } : ok ? { raise: 0.7 * (1 - prog(t, LS('ACE_ok') + 0.5, 0.4)) } : undefined,
    smile: sheepish ? 0.2 : 0.7, squint: aceGig ? 1 : 0, blush: sheepish || aceGig ? 0.7 : 0.2,
    tilt: aceGig ? Math.sin(t * 14) * 0.05 : ok ? Math.sin(prog(t, LE('ACE_ok') - 0.3, 0.6) * Math.PI * 2) * 0.06 : 0,
    hairBounce: aceGig ? Math.sin(t * 14) * 4 : 0,
  }, {
    wide: during(t, 'BB_repeat', 0, 0.1) ? 0.7 : 0, raise: during(t, 'BB_repeat') ? 1 : 0,
    happy: giggle ? 1 : 0, pose: giggle ? 'up' : 'rest',
  }, giggle ? Math.sin(t * 22) * 5 : 0, giggle ? -Math.abs(Math.sin(t * 11)) * 8 : 0);
  // dream wipe into the flashback
  const rOpen = easeInOut(prog(t, flash, 0.7)) * (1 - easeInOut(prog(t, flashEnd, 0.7)));
  if (rOpen > 0) {
    ctx.save();
    const cx = TWO.ax, cy = TWO.ay, r = rOpen * 1500;
    ctx.beginPath();
    for (let i = 0; i <= 48; i++) {
      const a = i / 48 * Math.PI * 2, rr = r + Math.sin(a * 9 + t * 4) * 14 * (rOpen < 1 ? 1 : 0);
      const px = cx + Math.cos(a) * rr, py = cy + Math.sin(a) * rr;
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    }
    ctx.closePath(); ctx.clip();
    const bt = t - flash;
    const rise = prog(t, flash + 0.6, 0.8) * (1 - prog(t, flashEnd - 0.4, 0.5));
    bedroomScene(ctx, t, {
      morning: 0, nails: { state: 'bitten', len: 7 }, zzz: 1,
      aceE: { closed: 1, smile: bt > 1.6 ? 0.0 : 0.35, brow: bt > 1.6 ? { worry: 0.5 } : undefined },
      baby: { rise, chomp: t > flash + 1.2 && t < flashEnd - 0.2 ? (Math.sin(t * 22) * 0.5 + 0.5) : 0, mood: 'mischief', tilt: 0.25 + Math.sin(t * 11) * 0.03 * (t > flash + 1.2 ? 1 : 0) },
    });
    // dreamy edge
    const g = ctx.createRadialGradient(360, 640, 380, 360, 640, 820);
    g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(1, 'rgba(255,255,255,0.85)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.restore();
    if (rOpen < 1) { // wobbly rim
      ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.strokeStyle = 'rgba(255,255,255,0.8)'; ctx.lineWidth = 16; ctx.stroke(); ctx.restore();
    }
  }
}

// thinking close-up of Blueberry (used after "Hmmm" and for "another idea")
function thinking(ctx, t, which) {
  B.starRoom(ctx, t, 1010, true);
  const t0 = which === 'brother' ? M('brother.hmm') : M('night1.another');
  const bulb = which === 'brother' ? M('brother.bulb') : t0 + 0.9;
  const lit = t > bulb;
  const bp = easeOutBack(prog(t, bulb, 0.35));
  const excited = which === 'brother' && during(t, 'BB_gloves', 0.1, 0.4);
  const bob = Math.sin(t * 2) * 6;
  ellipse(ctx, 360, 945, 170, 24); ctx.fillStyle = 'rgba(150,50,100,0.16)'; ctx.fill();
  drawBall(ctx, 360, 755 + bob - (excited ? Math.abs(Math.sin(t * 8)) * 20 : 0), 190, Math.sin(t * 0.8) * 0.15, {
    pose: lit ? (excited ? 'up' : 'point') : 'chin', look: lit ? [0, -0.2] : [0.5, -1], think: !lit, wide: lit ? 0.5 : 0,
    sparkle: lit ? 1 : 0, happy: excited && Math.sin(t * 3) > 0.6 ? 1 : 0,
  }, t);
  // thought bubbles + cloud
  P.thoughtDots(ctx, [[440, 560, 14], [480, 515, 20], [505, 465, 26]], t0 + 0.3, t);
  const cs = easeOutBack(prog(t, t0 + 0.8, 0.45));
  const cx = 360, cy = 270;
  P.thoughtCloud(ctx, cx, cy, 540, 330, cs);
  if (cs <= 0.05) return;
  ctx.save(); ctx.beginPath(); ctx.ellipse(cx, cy, 250 * cs, 150 * cs, 0, 0, Math.PI * 2); ctx.clip();
  if (which === 'brother') {
    const inIdea = t < LS('N_thought');
    const inQ = t >= LS('N_thought') && t < bulb;
    if (inIdea) { // the problem: baby brother nibbling nails
      ctx.save(); ctx.translate(270, 290); ctx.scale(0.75, 0.75);
      C.babyHead(ctx, { t, mood: 'mischief', chomp: Math.sin(t * 20) * 0.5 + 0.5, tilt: -0.15 });
      ctx.restore();
      drawHand(ctx, 450, 380, 0.85, 0.2, { nails: { state: 'bitten', len: 7, sore: 0.8 } }, t);
      // "no" sign appears while narrator says "stop biting"
      const ns = easeOutBack(prog(t, LE('N_idea') - 1.6, 0.35));
      if (ns > 0) {
        ctx.save(); ctx.translate(360, 270); ctx.scale(ns, ns); ctx.globalAlpha = 0.85;
        ctx.beginPath(); ctx.arc(0, 0, 130, 0, Math.PI * 2); ctx.strokeStyle = '#FF3B3B'; ctx.lineWidth = 18; ctx.stroke();
        ctx.beginPath(); ctx.moveTo(-92, -92); ctx.lineTo(92, 92); ctx.stroke();
        ctx.restore();
      }
    } else if (inQ) {
      for (let i = 0; i < 3; i++) {
        const qs = easeOutBack(prog(t, LS('N_thought') + i * 0.4, 0.3));
        if (qs > 0) P.qmark(ctx, 250 + i * 110, 290 - Math.abs(Math.sin(t * 5 + i)) * 30, 110 * qs, ['#8E5BD6', '#2F6BFF', '#FF5B8A'][i], (i - 1) * 0.2);
      }
    } else if (!(t > LS('BB_gloves') - 0.05)) {
      P.lightbulb(ctx, cx, cy - 10, 1.15 * bp, t, 1);
    } else { // gloves + moon = wear gloves to bed
      const gs = easeOutBack(prog(t, LS('BB_gloves') + 0.5, 0.35));
      drawHand(ctx, 290, 390, 0.95 * gs, -0.15, { glove: true }, t);
      drawHand(ctx, 430, 390, 0.95 * gs, 0.15, { glove: true, flip: -1 }, t);
      P.moon(ctx, 540, 200, 46 * gs);
      L.star(ctx, 190, 190, 20 * gs, 0); fillStroke(ctx, '#FFE14D', '#E0A800', 2);
    }
  } else {
    P.lightbulb(ctx, cx, cy - 10, 1.15 * bp, t, 1);
  }
  ctx.restore();
}

// ========================================================== NIGHT 1 =====
function night1(ctx, t) {
  const hot0 = M('night1.hot'), another = M('night1.another');
  if (t >= another) return thinking(ctx, t, 'night1');
  if (t >= hot0) return hotHands(ctx, t, hot0);
  const morning = smooth(prog(t, M('night1.morning'), 2.2));
  const baby0 = M('night1.baby');
  const huh = LS('BABY_huh');
  const rise = prog(t, baby0, 0.8) * (1 - prog(t, huh + 1.3, 0.7));
  const wake = M('night1.wake');
  const awake = t > wake + 0.3;
  const yawn = pulse(t, wake + 0.5, 1.3);
  const peel = prog(t, M('night1.glovesOff') - 0.9, 1.0);
  const fine = t > LS('N_fine');
  bedroomScene(ctx, t, {
    morning, gloves: peel <= 0, glovePeel: peel > 0 && peel < 1 ? peel : 0,
    nails: { state: 'bitten', len: 8 }, zzz: 1 - morning,
    aceE: awake ? { closed: 0, smile: 0.4, open: yawn * 0.9, round: yawn, look: fine ? [0.9, 0.6] : [0.3, -0.2] } : { closed: 1, smile: 0.35 },
    baby: { rise, mood: t > huh - 0.1 ? 'huh' : 'mischief', chomp: t > baby0 + 0.9 && t < huh - 0.2 ? Math.max(0, Math.sin((t - baby0) * 9)) * 0.6 : 0, look: t > huh ? [-0.9, 0.5] : [-0.8, 0.4] },
  });
  if (rise > 0 && t > huh - 0.1) P.qmark(ctx, 640, 640 - (1 - rise) * 300 - Math.abs(Math.sin(t * 4)) * 12, 90, '#FFFFFF', 0.15);
  if (fine) { // nails are fine: sparkles + tick
    for (const tp of C.handTips({ spread: 0.6 })) {
      const c = Math.cos(BH.rot), s = Math.sin(BH.rot);
      const x = BH.x + (tp.x * c - tp.y * s) * BH.s, y = BH.y + (tp.x * s + tp.y * c) * BH.s;
      L.sparkle(ctx, x, y, 12 * Math.abs(Math.sin(t * 5 + tp.x)), '#FFFFFF', window(t, LS('N_fine'), 0.3, LE('N_fine') + 0.6, 0.3));
    }
    P.checkBadge(ctx, 600, 660, 0.6 * easeOutBack(prog(t, LS('N_fine') + 0.8, 0.35)) * (1 - prog(t, LS('N_but'), 0.25)));
  }
}

// Ace sitting up in bed, hands up (used for hot hands and for hooray)
function sittingAce(ctx, t, morning, e, hands, bob = 0) {
  B.bedroom(ctx, t, morning);
  drawAce(ctx, 360, 440 + bob, 1.2, e, t, { shirt: '#B9A3F0' });
  for (const h of hands) drawHand(ctx, h.x, h.y + bob, h.s || 1.05, h.rot || 0, { arm: 260, sleeve: '#B9A3F0', armSleeveY: 50, ...h.o }, t);
  B.blanket(ctx, t, morning, 905);
}
function hotHands(ctx, t, t0) {
  const fan = Math.sin(t * 11) * 0.22;
  const dislike = during(t, 'ACE_dislike', 0.1, 0.8);
  const lower = easeInOut(prog(t, LE('ACE_dislike') + 0.2, 0.6));
  sittingAce(ctx, t, 1, {
    flush: dislike ? 0.5 : 0.9, brow: dislike ? { angry: 0.5, worry: 0.3 } : { worry: 1 },
    smile: dislike ? -0.7 : -0.4, wavy: !L.talking('ACE', t) && !dislike, look: dislike ? [-0.7, 0.1] : [0, 0.6],
    blush: 0.8, tilt: dislike ? -0.08 : 0,
  }, [
    { x: 140, y: 830 + lower * 300, rot: -0.25 + fan, o: { hot: 1, nails: { len: 9 } } },
    { x: 580, y: 830 + lower * 300, rot: 0.25 - fan, o: { hot: 1, flip: -1, nails: { len: 9 } } },
  ]);
  // sweat drop on the forehead
  const d = (t * 0.8) % 1;
  ctx.save(); ctx.globalAlpha = Math.sin(d * Math.PI);
  const x = 470, y = 330 + d * 40;
  ctx.beginPath(); ctx.moveTo(x, y - 18); ctx.quadraticCurveTo(x + 12, y, x, y + 7); ctx.quadraticCurveTo(x - 12, y, x, y - 18); ctx.fillStyle = '#8FD8FF'; ctx.fill();
  ctx.restore();
}

// ============================================================ BLUE =====
const OR = { hz: 660, ax: 280, ay: 350, as: 1.2, hx: 540, hy: 790, hs: 1.75 };
function wallGloves(ctx, t) {
  for (const s of [-1, 1]) drawHand(ctx, 620 + s * 34, 290, 0.42, s * 0.25, { glove: true, flip: s }, t);
}
function blue(ctx, t) {
  const paint = M('blue.paint'), pretty = M('blue.pretty');
  if (t >= pretty) return admire(ctx, t, pretty);
  if (t >= paint) return paintCloseUp(ctx, t, paint + 0.6, NAILS_BLUE, 0.8);
  room(ctx, t, 'orange', OR.hz);
  wallGloves(ctx, t);
  const bs = M('blue.blueSay');
  const blueYes = t > bs && t < bs + 1.6;
  const like = during(t, 'ACE_like', 0.1, 0.6);
  drawAce(ctx, OR.ax, OR.ay, OR.as, {
    look: lookAt(OR.ax, OR.ay, OR.hx, OR.hy - 60), sparkle: blueYes ? 1 : 0, smile: blueYes || like ? 0.95 : 0.65,
    open: blueYes ? 0.3 : 0, brow: during(t, 'BB_paint', 0, 0.2) ? { raise: 0.6 } : undefined,
    squint: like && t > LE('ACE_like') ? 1 : 0, tilt: like ? Math.sin(t * 9) * 0.06 : 0, blush: blueYes ? 0.6 : 0.25,
  }, t);
  P.sparkleBurst(ctx, OR.ax, OR.ay, t, bs, '#5FA8FF', 10, 230, 1.3);
  P.sparkleBurst(ctx, OR.ax, OR.ay, t, bs + 0.15, '#2F6BFF', 7, 170, 1.2);
  // Blueberry on the rug, holding up the polish
  const bot = M('blue.bottle');
  const hold = t > bot + 0.3;
  ellipse(ctx, OR.hx, OR.hy + 112, 100, 16); ctx.fillStyle = 'rgba(70,110,160,0.2)'; ctx.fill();
  drawHamster(ctx, OR.hx, OR.hy, OR.hs, { look: [-0.6, -0.8], pose: hold ? 'hold' : 'rest', happy: like ? 1 : 0, squash: pulse(t, bot + 0.25, 0.25) }, t);
  const ps = easeOutBack(prog(t, bot + 0.3, 0.35));
  if (ps > 0) {
    P.polishBottle(ctx, OR.hx + 6, OR.hy + 52 - ps * 26, 1.1 * ps);
    L.sparkle(ctx, OR.hx + 52, OR.hy - 30, 16 * Math.abs(Math.sin(t * 4)), '#FFFFFF', ps);
  }
  // little thought: baby + yucky taste
  const ts = easeOutBack(prog(t, M('blue.taste') + 1.5, 0.4)) * (1 - prog(t, LE('BB_taste') + 0.3, 0.3));
  if (ts > 0) {
    P.thoughtDots(ctx, [[560, 700, 9], [585, 670, 13]], M('blue.taste') + 1.2, t);
    P.thoughtCloud(ctx, 560, 545, 270, 190, ts);
    ctx.save(); ctx.translate(560, 548); ctx.scale(0.62 * ts, 0.62 * ts);
    C.babyHead(ctx, { t, mood: 'yuck', green: 0.8, tilt: Math.sin(t * 20) * 0.08 });
    ctx.restore();
    P.stinkLines(ctx, 560, 500, t, ts * 0.8);
  }
}

// big hand close-up with Blueberry painting each nail
function paintCloseUp(ctx, t, p0, colours, step, baseColours = null, label = null) {
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, '#FFCF5C'); g.addColorStop(1, '#FFB347');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#BFD9F2'; ctx.fillRect(0, 1060, W, H - 1060);
  const hx = 360, hy = 1250, hs = 3.8;
  const fills = [0, 1, 2, 3, 4].map(i => smooth(prog(t, p0 + i * step + step * 0.45, step * 0.45)));
  const cols = colours.slice();
  // paint over a previous colour: draw base first by setting fill 1 for base, then overlay
  drawHand(ctx, hx, hy, hs, 0, { nails: { len: 15, colours: baseColours || cols, fill: baseColours ? ONES : fills }, arm: 300, sleeve: '#39C3C6', armSleeveY: 70, spread: 0.9 }, t);
  if (baseColours) { // overlay new colours on top of the old ones
    ctx.save(); ctx.translate(hx, hy); ctx.scale(hs, hs);
    const tips = C.handTips({ spread: 0.9 });
    tips.forEach((tp, i) => {
      if (fills[i] <= 0) return;
      ctx.save(); ctx.beginPath(); ctx.ellipse(tp.x, tp.y + 1, 7, 9, i === 0 ? -0.74 : 0, 0, Math.PI * 2); ctx.clip();
      ctx.fillStyle = cols[i]; ctx.fillRect(tp.x - 10, tp.y + 12 - 24 * fills[i], 20, 24 * fills[i]);
      ctx.restore();
    });
    ctx.restore();
  }
  // Blueberry hops from nail to nail with a brush
  const tips = C.handTips({ spread: 0.9 }).map(tp => ({ x: hx + tp.x * hs, y: hy + tp.y * hs }));
  const idx = clamp(Math.floor((t - p0) / step), 0, 4);
  const local = (t - p0) / step - idx;
  const prev = tips[Math.max(0, idx - 1)], cur = tips[idx];
  const spot = tp => ({ x: tp.x + 78, y: tp.y + 92 });
  let pos;
  if (t < p0) pos = { x: 625, y: 770 };
  else if (t > p0 + step * 5) pos = { x: lerp(spot(tips[4]).x, 625, easeInOut(prog(t, p0 + step * 5, 0.5))), y: lerp(spot(tips[4]).y, 770, easeInOut(prog(t, p0 + step * 5, 0.5))) };
  else {
    const a = idx === 0 ? { x: 625, y: 770 } : spot(prev), b = spot(cur);
    const h = clamp(local / 0.4);
    pos = { x: lerp(a.x, b.x, easeInOut(h)), y: lerp(a.y, b.y, easeInOut(h)) - Math.sin(h * Math.PI) * 70 };
  }
  const painting = t >= p0 && t <= p0 + step * 5 && local > 0.4;
  const done = t > p0 + step * 5;
  const s = 1.05;
  drawHamster(ctx, pos.x, pos.y, s, { pose: done ? 'up' : 'hold', happy: done ? 1 : 0, look: [-0.8, -0.6], squash: painting ? 0.3 * Math.abs(Math.sin(t * 14)) : 0 }, t);
  if (!done) {
    const tip = t < p0 ? { x: pos.x - 30, y: pos.y - 60 } : { x: cur.x + (painting ? Math.sin(t * 16) * 4 : 12), y: cur.y + (painting ? Math.cos(t * 16) * 6 : 14) };
    P.brush(ctx, pos.x - 4, pos.y + 6, tip.x, tip.y, cols[idx]);
  }
  // sparkle on each finished nail
  tips.forEach((tp, i) => {
    const fin = p0 + i * step + step * 0.9;
    P.sparkleBurst(ctx, tp.x, tp.y, t, fin, '#FFFFFF', 6, 50, 0.6);
  });
  if (label) label(ctx, t);
}

function admire(ctx, t, t0) {
  room(ctx, t, 'orange', OR.hz);
  wallGloves(ctx, t);
  const up = easeOutBack(prog(t, t0 - 0.1, 0.5));
  const hx = 560, hy = 1060 - up * 330;
  drawAce(ctx, OR.ax + 20, OR.ay + 20, OR.as, { look: lookAt(OR.ax, OR.ay, hx, hy - 120), sparkle: 1, smile: 0.95, blush: 0.6 }, t);
  drawHand(ctx, hx, hy, 1.15, 0.12, { nails: { len: 10, colours: NAILS_BLUE, fill: ONES }, arm: 200, sleeve: '#39C3C6', armSleeveY: 70, wiggle: 1 }, t);
  C.handTips({}).forEach((tp, i) => {
    const c = Math.cos(0.12), s = Math.sin(0.12);
    const x = hx + (tp.x * c - tp.y * s) * 1.15, y = hy + (tp.x * s + tp.y * c) * 1.15;
    L.sparkle(ctx, x + 8, y - 10, 14 * Math.max(0, Math.sin(t * 6 + i * 1.3)), '#FFFFFF', up);
  });
}

// ========================================================== NIGHT 2 =====
function night2(ctx, t) {
  const check = M('night2.check'), grow = M('night2.grow'), tap = M('night2.tap');
  if (t >= tap) return happyTap(ctx, t, tap);
  if (t >= grow) return growCloseUp(ctx, t, grow);
  if (t >= LS('ACE_yay') - 0.1) return hooray(ctx, t);
  if (t >= check) return checkCloseUp(ctx, t, check);
  const morning = smooth(prog(t, M('night2.morning'), 2.0));
  const baby0 = M('night2.baby'), bleh = M('night2.bleh');
  const rise = prog(t, baby0, 0.8) * (1 - prog(t, bleh + 1.3, 0.5));
  const yuck = t > bleh - 0.05;
  bedroomScene(ctx, t, {
    morning, nails: { len: 8, colours: NAILS_BLUE, fill: ONES }, zzz: 1 - morning,
    aceE: { closed: 1, smile: 0.4 },
    baby: { rise, mood: yuck ? 'yuck' : 'mischief', green: yuck ? 0.8 : 0, chomp: !yuck && t > baby0 + 0.9 ? Math.max(0, Math.sin((t - baby0) * 9)) * 0.6 : 0,
      tilt: 0.25 + (yuck ? Math.sin(t * 24) * 0.14 * (1 - prog(t, bleh + 0.9, 0.3)) : 0) },
  });
  if (yuck && rise > 0) P.stinkLines(ctx, 640, 680, t, rise);
}
function softBg(ctx, c1 = '#FFF4D6', c2 = '#FFD9A8') {
  const g = ctx.createRadialGradient(360, 600, 60, 360, 600, 760);
  g.addColorStop(0, c1); g.addColorStop(1, c2);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
function checkCloseUp(ctx, t, t0) {
  softBg(ctx, '#EAF6FF', '#BFE3FF');
  drawHand(ctx, 370, 1250, 3.9, 0, { nails: { len: 8, colours: NAILS_BLUE, fill: ONES }, arm: 300, sleeve: '#B9A3F0', armSleeveY: 60 }, t);
  C.handTips({}).forEach((tp, i) => L.sparkle(ctx, 370 + tp.x * 3.9 + 20, 1250 + tp.y * 3.9 - 28, 18 * Math.max(0, Math.sin(t * 5 + i)), '#FFFFFF'));
  P.checkBadge(ctx, 560, 240, 1.1 * easeOutBack(prog(t, t0 + 0.9, 0.4)));
}
function hooray(ctx, t) {
  const p = t - LS('ACE_yay');
  const bob = -Math.abs(Math.sin(p * 7)) * 18 * (1 - prog(p, 1.4, 0.4));
  sittingAce(ctx, t, 1, { squint: 1, smile: 1, open: 0.4, blush: 0.6, hairBounce: bob * 0.3 }, [
    { x: 140, y: 760, rot: -0.3 + Math.sin(t * 10) * 0.12, o: { nails: { len: 9, colours: NAILS_BLUE, fill: ONES } } },
    { x: 580, y: 760, rot: 0.3 - Math.sin(t * 10) * 0.12, o: { flip: -1, nails: { len: 9, colours: NAILS_BLUE, fill: ONES } } },
  ], bob);
  P.sparkleBurst(ctx, 360, 440, t, LS('ACE_yay'), '#FFFFFF', 10, 300, 1.2);
}
function growCloseUp(ctx, t, t0) {
  softBg(ctx, '#FFF7E6', '#FFE0B8');
  const g = smooth(prog(t, t0 + 0.6, 4.6));
  drawHand(ctx, 370, 1250, 3.9, 0, { nails: { state: g < 0.35 ? 'bitten' : 'normal', len: lerp(8, 17, g), colours: NAILS_BLUE, fill: ONES, sore: 0.5 * (1 - g) }, arm: 300, sleeve: '#39C3C6', armSleeveY: 60 }, t);
  // calendar pages flipping in the corner
  const day = Math.min(10, 1 + Math.floor(clamp((t - t0 - 0.4) / 0.45, 0, 9)));
  const flip = ((t - t0 - 0.4) / 0.45) % 1;
  ctx.save(); ctx.translate(570, 200); ctx.rotate(0.06);
  ctx.beginPath(); ctx.roundRect(-90, -90, 180, 190, 18); fillStroke(ctx, '#FFFFFF', '#3B2F55', 4);
  ctx.save(); ctx.beginPath(); ctx.roundRect(-90, -90, 180, 190, 18); ctx.clip(); ctx.fillStyle = '#FF4F6E'; ctx.fillRect(-90, -90, 180, 46); ctx.restore();
  ctx.font = '30px FredokaB'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#FFFFFF'; ctx.fillText('DAY', 0, -66);
  ctx.font = '84px "Luckiest Guy"'; ctx.fillStyle = '#3B2F55'; ctx.fillText(String(day), 0, 38);
  if (day < 10 && t > t0 + 0.4 && flip < 0.35) { // page lifting
    const k = flip / 0.35;
    ctx.save(); ctx.beginPath(); ctx.moveTo(-90, -44); ctx.lineTo(90, -44); ctx.lineTo(90, -44 + 144 * (1 - k)); ctx.lineTo(-90, -44 + 144 * (1 - k)); ctx.closePath();
    ctx.fillStyle = 'rgba(255,255,255,0.9)'; ctx.fill(); ctx.restore();
  }
  ctx.restore();
  // little growth arrows next to the nails
  if (g > 0.05 && g < 0.98) {
    ctx.save(); ctx.strokeStyle = '#4CD964'; ctx.lineWidth = 7; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (const i of [1, 2, 3]) {
      const tp = C.handTips({})[i]; const x = 370 + tp.x * 3.9 + 62, y = 1250 + tp.y * 3.9 - ((t * 60) % 40);
      ctx.globalAlpha = 0.8; ctx.beginPath(); ctx.moveTo(x, y + 30); ctx.lineTo(x, y - 10); ctx.moveTo(x - 12, y + 2); ctx.lineTo(x, y - 10); ctx.lineTo(x + 12, y + 2); ctx.stroke();
    }
    ctx.restore();
  }
}
function happyTap(ctx, t, t0) {
  room(ctx, t, 'star', TWO.hz);
  const contact = TWO.bx - TWO.R - 175 + 2;
  const tapT = t0 + 0.9;
  let hx = lerp(-260, contact - 60, easeOut(prog(t, t0 + 0.1, 0.6)));
  hx = lerp(hx, contact, pulse(t, tapT - 0.25, 0.5));
  const hooray = during(t, 'BB_hooray', 0.1, 0.5);
  if (t > LS('ACE_noooch')) hx = lerp(contact - 60, -40, easeInOut(prog(t, LS('ACE_noooch'), 0.4)));
  let bx = TWO.bx + 30 * easeOut(prog(t, tapT, 0.4)) * (1 - easeInOut(prog(t, tapT + 0.5, 0.6)));
  const hop = hooray ? Math.sin(clamp((t - LS('BB_hooray') + 0.1) / 0.7) * Math.PI) * 80 : 0;
  const after = t > tapT + 0.2;
  drawAce(ctx, TWO.ax, TWO.ay, TWO.as, {
    look: after ? [0.6, 0.5] : lookAt(TWO.ax, TWO.ay, hx + 175, 760), smile: 0.9, squint: t > LE('ACE_noooch') ? 1 : 0,
    brow: after && t < LS('ACE_noooch') + 0.4 ? { raise: 0.8 } : undefined, blush: 0.5, sparkle: after && t < LE('ACE_noooch') ? 1 : 0,
  }, t);
  ellipse(ctx, bx, TWO.by + TWO.R * 0.96, TWO.R * 0.8 * (1 - hop / 300), 14); ctx.fillStyle = 'rgba(150,50,100,0.16)'; ctx.fill();
  drawBall(ctx, bx, TWO.by - hop, TWO.R, (bx - TWO.bx) / TWO.R, { look: [-0.8, -0.4], happy: hooray ? 1 : 0, pose: hooray ? 'up' : 'rest' }, t);
  // pointing hand with long healthy blue nails (up-tilted when showing)
  const show = easeInOut(prog(t, LS('ACE_noooch'), 0.4));
  ctx.save(); ctx.translate(hx, 770); ctx.scale(1.35, 1.35); ctx.rotate(-0.12);
  C.pointHand(ctx, { nails: { len: 16, colour: BLUE } });
  ctx.restore();
  if (show > 0) drawHand(ctx, 140, 1100 - show * 330, 1.1, -0.15, { nails: { len: 16, colours: NAILS_BLUE, fill: ONES }, arm: 260, sleeve: '#39C3C6', armSleeveY: 70, wiggle: 1 }, t);
  if (t > tapT && t < tapT + 0.5) L.sparkle(ctx, contact + 175 + 10, 750, 26 * pulse(t, tapT, 0.5), '#FFFFFF');
}

// ========================================================= TUESDAY =====
const RAINBOW = ['#FF4B4B', '#FF9F1C', '#FFE135', '#3DDC84', '#9B5DE5'];
function tuesday(ctx, t) {
  const thanks = M('tuesday.thanks');
  if (t >= thanks) return thanksShot(ctx, t, thanks);
  if (t >= LS('N_any') - 0.05) return colourMontage(ctx, t);
  // calendar card: Tuesday night after dinner
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, '#1E3F86'); g.addColorStop(1, '#5B4A9A');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const r = L.rng(5);
  for (let i = 0; i < 14; i++) B.faceStar(ctx, r() * W, 60 + r() * 1100, 12 + r() * 8 + Math.sin(t * 2 + i) * 1.5, Math.sin(t + i) * 0.2, true);
  P.moon(ctx, 600, 150, 70);
  const c0 = M('tuesday.cal');
  const cp = easeOutBounce(prog(t, c0, 0.9));
  P.calendar(ctx, 360, 560 - (1 - cp) * 900, 1, 'TUESDAY', 'after dinner', t);
  P.plate(ctx, 360, 610 - (1 - cp) * 900, 0.95 * easeOutBack(prog(t, c0 + 1.0, 0.4)));
}
function colourMontage(ctx, t) {
  const c1 = M('tuesday.c1'), c2 = M('tuesday.c2'), c3 = M('tuesday.c3');
  const PINK = ['#FF5FA2', '#FF5FA2', '#FF5FA2', '#FF5FA2', '#FF5FA2'];
  const GREEN = ['#3DDC84', '#3DDC84', '#3DDC84', '#3DDC84', '#3DDC84'];
  let base = NAILS_BLUE, cols = PINK, p0 = c1 + 0.55, n = 1;
  if (t >= c3) { base = GREEN; cols = RAINBOW; p0 = c3 + 0.75; n = 3; }
  else if (t >= c2) { base = PINK; cols = GREEN; p0 = c2 + 0.55; n = 2; }
  const label = (ctx2, tt) => {
    ctx2.save(); ctx2.translate(170, 170); ctx2.rotate(-0.06);
    ctx2.beginPath(); ctx2.roundRect(-130, -60, 260, 120, 22); fillStroke(ctx2, '#FFFFFF', '#3B2F55', 5);
    ctx2.font = '58px "Luckiest Guy"'; ctx2.textAlign = 'center'; ctx2.textBaseline = 'middle'; ctx2.fillStyle = '#FF4F6E';
    ctx2.fillText('TUESDAY', 0, 6);
    ctx2.restore();
    for (let i = 0; i < n; i++) { L.star(ctx2, 60 + i * 50, 262, 18, 0); fillStroke(ctx2, '#FFE14D', '#E0A800', 2); }
  };
  paintCloseUp(ctx, t, t < c1 ? 1e9 : p0, cols, 0.22, base, label);
}
function thanksShot(ctx, t, t0) {
  room(ctx, t, 'star', TWO.hz);
  const hugging = t > LE('ACE_thanks');
  drawAce(ctx, TWO.ax, TWO.ay, TWO.as, { look: lookAt(TWO.ax, TWO.ay, TWO.bx, TWO.by), smile: 0.95, blush: 0.9, squint: hugging && !L.talking('BB', t) ? 1 : 0, tilt: 0.06 }, t);
  drawHand(ctx, 140, 1080 - easeOutBack(prog(t, t0, 0.5)) * 300, 1.1, -0.2 + Math.sin(t * 8) * 0.18 * (t < LE('ACE_thanks') ? 1 : 0),
    { nails: { len: 16, colours: RAINBOW, fill: ONES }, arm: 260, sleeve: '#39C3C6', armSleeveY: 70 }, t);
  ellipse(ctx, TWO.bx, TWO.by + TWO.R * 0.96, TWO.R * 0.8, 14); ctx.fillStyle = 'rgba(150,50,100,0.16)'; ctx.fill();
  drawBall(ctx, TWO.bx, TWO.by - Math.abs(Math.sin(t * 3)) * 10 * (hugging ? 1 : 0), TWO.R, Math.sin(t * 3) * 0.1, { look: [-0.7, -0.6], pose: during(t, 'BB_welcome') ? 'wave' : 'rest', happy: t > LE('BB_welcome') ? 1 : 0 }, t);
  P.floatingHearts(ctx, 400, 700, t, LS('ACE_thanks') + 0.5, window(t, LS('ACE_thanks') + 0.5, 0.4, SC.tuesday.end + 1, 0.3), 12, 380);
}

// ============================================================= END =====
function end(ctx, t) {
  const lt = t - SC.end.start, dur = SC.end.end - SC.end.start;
  B.stageBack(ctx, t);
  const ns = LS('N_end') - 0.35;
  const tp = easeOutBounce(prog(t, ns, 0.8));
  if (tp > 0) {
    ctx.save(); ctx.translate(440, 470 - (1 - tp) * 600);
    ctx.font = '84px FredokaB'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round'; ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 14; ctx.strokeText('THE END', 0, 0);
    ctx.fillStyle = '#1F1A33'; ctx.fillText('THE END', 0, 0);
    ctx.restore();
  }
  P.bow(ctx, 440, 690, 1.15 * L.easeOutElastic(prog(t, ns + 0.6, 1.1)));
  // Ace + Blueberry peek in and wave
  const pk = easeOutBack(prog(lt, 2.4, 0.7));
  if (pk > 0) {
    drawAce(ctx, 220 + 0 * pk, 1250 - pk * 330, 0.85, { look: [0.4, -0.2], smile: 0.9, wink: pulse(lt, 4.4, 0.6) > 0.25 ? 1 : 0, blush: 0.5 }, t);
    drawHand(ctx, 60, 1300 - pk * 330, 0.9, -0.3 + Math.sin(t * 9) * 0.25, { nails: { len: 16, colours: RAINBOW, fill: ONES }, arm: 200, sleeve: '#39C3C6', armSleeveY: 60 }, t);
    drawBall(ctx, 560, 1110 - pk * 150 - Math.abs(Math.sin(t * 4)) * 16, 80, Math.sin(t * 4) * 0.1, { look: [-0.4, -0.5], pose: 'wave', happy: 1 }, t);
  }
  const open = easeInOut(prog(lt, 0.1, 1.4)) * (1 - easeInOut(prog(lt, dur - 2.1, 1.4)));
  B.stageFront(ctx, t, open);
}

const SCENE_FN = { title, hello, roll, ooch, brother, night1, blue, night2, tuesday, end };
module.exports = { SCENE_FN, SC };
