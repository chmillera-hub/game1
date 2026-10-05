/* EMOTIONAL CHAD - people rig (Goku, Chad, villagers, the universe martial artist), sets and FX. */
(function () {
  'use strict';
  const { W, H, TAU, clamp, lerp, hash, noise, ellipse, circle, rrect, text, mix, rgba, applyCam, FONT_TITLE } = F;
  const A = window.A;
  const C = A.C, OUT = A.OUT;

  function ik(sx, sy, tx, ty, L1, L2, bend) {
    const dx = tx - sx, dy = ty - sy;
    const d = clamp(Math.hypot(dx, dy), Math.abs(L1 - L2) + 0.5, L1 + L2 - 0.5);
    const a = Math.atan2(dy, dx);
    const c = clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1);
    const a1 = a + bend * Math.acos(c);
    const ex = sx + L1 * Math.cos(a1), ey = sy + L1 * Math.sin(a1);
    const a2 = Math.atan2(ty - ey, tx - ex);
    return { ex, ey, hx: ex + L2 * Math.cos(a2), hy: ey + L2 * Math.sin(a2), a2 };
  }
  function limb(ctx, sx, sy, j, w, col, outline) {
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = outline; ctx.lineWidth = w + 8;
    ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(j.ex, j.ey); ctx.lineTo(j.hx, j.hy); ctx.stroke();
    ctx.strokeStyle = col; ctx.lineWidth = w;
    ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(j.ex, j.ey); ctx.lineTo(j.hx, j.hy); ctx.stroke();
  }

  // ------------------------------------------------------------------ outfits
  const KINDS = {
    goku: { skin: '#f4c9a0', top: '#f47a1f', top2: '#d9620f', pants: '#f47a1f', shoe: '#2a4fa0', cuff: '#2a4fa0', belt: '#2a4fa0', under: '#2a4fa0', width: 1.08 },
    chad: { skin: '#f0c4a0', top: '#8f97a3', top2: '#767e8a', pants: '#2f3b56', shoe: '#f2f2f2', cuff: '#7c838e', width: 1.14, belly: 1 },
    alien: { skin: '#5fa8c9', top: '#f1ece2', top2: '#d6cfc0', pants: '#f1ece2', shoe: '#7a2a2a', cuff: '#5fa8c9', belt: '#c8322b', under: '#f1ece2', width: 1.05 },
    villager: { skin: '#e0b08c', top: '#5f8a7a', top2: '#4a6e61', pants: '#6b5a48', shoe: '#4a3020', cuff: '#4a6e61', width: 1.0 },
  };

  /** standard hand targets (body space, feet at 0) */
  A.PP = {
    idle: { r: [58, -108], l: [-58, -108], rb: -1, lb: 1 },
    cross: { r: [-34, -214], l: [34, -204], rb: -1, lb: 1, cross: true },
    power: { r: [92, -150], l: [-92, -150], rb: 1, lb: -1, fists: true },
    yellUp: { r: [130, -330], l: [-130, -330], rb: 1, lb: -1, fists: true },
    handUp: { r: [92, -330], l: [-40, -190], rb: 1, lb: 1 },
    hipsBend: { r: [40, -160], l: [-40, -160], rb: -1, lb: 1 },
    explain: { r: [104, -220], l: [-80, -150], rb: -1, lb: 1 },
    shrug: { r: [130, -215], l: [-130, -215], rb: 1, lb: -1 },
    phone: { r: [60, -300], l: [-58, -108], rb: 1, lb: 1 },
    cup: { r: [120, -330], l: [-120, -330], rb: 1, lb: -1 },
    wave: { r: [128, -380], l: [-72, -135], rb: 1, lb: 1 },
    waveOff: { r: [130, -250], l: [-34, -204], rb: -1, lb: 1 },
    heart: { r: [12, -238], l: [-72, -135], rb: -1, lb: 1 },
    jog: { r: [60, -190], l: [-60, -190], rb: -1, lb: 1 },
    punch: { r: [190, -250], l: [-50, -230], rb: -1, lb: 1, fists: true },
    putt: { r: [18, -150], l: [-6, -160], rb: -1, lb: 1 },
    watch: { r: [-6, -228], l: [-20, -236], rb: -1, lb: 1 },
    waveBack: { r: [72, -130], l: [-150, -280], rb: -1, lb: -1 },
    thumbs: { r: [110, -250], l: [-72, -135], rb: 1, lb: 1, fists: true },
    listen: { r: [20, -280], l: [-34, -204], rb: 1, lb: 1 },
  };
  A.mixPP = function (p, q, k) {
    if (k <= 0) return p;
    if (k >= 1) return q;
    return {
      r: [lerp(p.r[0], q.r[0], k), lerp(p.r[1], q.r[1], k)], l: [lerp(p.l[0], q.l[0], k), lerp(p.l[1], q.l[1], k)],
      rb: k < 0.5 ? p.rb : q.rb, lb: k < 0.5 ? p.lb : q.lb, cross: (k < 0.5 ? p : q).cross, fists: (k < 0.5 ? p : q).fists,
    };
  };

  // ------------------------------------------------------------------ hair
  function gokuHair(ctx, hy, o, front) {
    const sup = o.super || 0, lvl = o.level || 0;
    const col = C(mix('#1b1b22', '#ffd23a', sup)), hi = C(mix('#3a3a48', '#fff2a0', sup));
    const outline = C(OUT);
    const t = o.t || 0;
    const flick = (i) => Math.sin(t * (sup > 0.5 ? 18 : 2) + i * 1.7) * (sup > 0.5 ? 4 : 1);
    if (!front) {
      // the long mane (level 3+) hangs behind the body
      if (lvl > 0.01) {
        const len = 260 * clamp(lvl);
        ctx.beginPath();
        ctx.moveTo(-56, hy - 30);
        for (let i = 0; i <= 8; i++) {
          const x = -64 + i * 16;
          ctx.lineTo(x + (i % 2 ? 10 : -6), hy + 20 + len * (0.75 + 0.25 * Math.sin(i * 2.1)) + flick(i));
          ctx.lineTo(x + 8, hy + 10 + len * 0.55);
        }
        ctx.lineTo(70, hy - 30);
        ctx.closePath();
        ctx.fillStyle = col; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 5; ctx.lineJoin = 'round'; ctx.stroke();
      }
      // back spikes
      const up = lerp(0, 1, sup);
      const spikes = [[-60, -10, -110, -40], [-50, -40, -96, -110], [-26, -56, -50, -150 - 30 * up], [4, -60, 6, -170 - 40 * up],
        [30, -56, 62, -150 - 30 * up], [52, -40, 104, -104], [62, -10, 118, -36]];
      ctx.beginPath();
      ctx.moveTo(-64, hy + 10);
      for (const [bx, by, tx, ty] of spikes) {
        ctx.lineTo(bx - 14, hy + by + 10);
        ctx.lineTo(lerp(tx, bx * 0.6, up * 0.3) + flick(bx), hy + ty + flick(by));
        ctx.lineTo(bx + 14, hy + by + 6);
      }
      ctx.lineTo(66, hy + 10);
      ctx.closePath();
      ctx.fillStyle = col; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 5; ctx.stroke();
      return;
    }
    // bangs over the forehead
    const bangs = sup > 0.5 ? [[-30, -12, -20, 0], [-6, -30, 10, -8], [18, -28, 34, -6]] : [[-36, -18, -40, 12], [-10, -34, -14, 4], [16, -30, 30, 10]];
    ctx.beginPath();
    ctx.moveTo(-46, hy - 30);
    for (const [bx, by, tx, ty] of bangs) {
      ctx.lineTo(bx - 10, hy + by);
      ctx.lineTo(tx, hy + ty);
      ctx.lineTo(bx + 14, hy + by - 4);
    }
    ctx.lineTo(46, hy - 30);
    ctx.quadraticCurveTo(0, hy - 64, -46, hy - 30);
    ctx.closePath();
    ctx.fillStyle = col; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4.5; ctx.stroke();
    ctx.strokeStyle = hi; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(-20, hy - 44); ctx.lineTo(-4, hy - 50); ctx.stroke();
  }
  function chadHair(ctx, hy) {
    const outline = C(OUT), col = C('#6b4a2e');
    const pts = [[-38, -36, 18], [-18, -50, 20], [6, -54, 20], [30, -46, 18], [42, -28, 14], [-44, -18, 12]];
    ctx.fillStyle = outline;
    for (const [x, y, r] of pts) { circle(ctx, x, hy + y, r + 4); ctx.fill(); }
    ctx.fillStyle = col;
    for (const [x, y, r] of pts) { circle(ctx, x, hy + y, r); ctx.fill(); }
    ctx.strokeStyle = outline; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(-6, hy - 40); ctx.quadraticCurveTo(4, hy - 24, -2, hy - 16); ctx.stroke();
  }
  function villagerHair(ctx, hy, o) {
    const outline = C(OUT), col = C(o.hair || '#3a2a20');
    const style = o.hairStyle || 0;
    ctx.beginPath();
    if (style === 1) { // long
      ctx.moveTo(-48, hy + 40); ctx.quadraticCurveTo(-56, hy - 50, 0, hy - 56); ctx.quadraticCurveTo(56, hy - 50, 48, hy + 40);
      ctx.lineTo(36, hy + 40); ctx.quadraticCurveTo(40, hy - 20, 0, hy - 30); ctx.quadraticCurveTo(-40, hy - 20, -36, hy + 40); ctx.closePath();
    } else if (style === 2) { // bun
      circle(ctx, 0, hy - 60, 18);
      ctx.moveTo(-44, hy - 6); ctx.quadraticCurveTo(-46, hy - 54, 0, hy - 52); ctx.quadraticCurveTo(46, hy - 54, 44, hy - 6); ctx.quadraticCurveTo(0, hy - 36, -44, hy - 6);
    } else { // short
      ctx.moveTo(-44, hy - 4); ctx.quadraticCurveTo(-46, hy - 56, 0, hy - 54); ctx.quadraticCurveTo(46, hy - 56, 44, hy - 4); ctx.quadraticCurveTo(10, hy - 34, -44, hy - 4);
    }
    ctx.fillStyle = col; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
  }

  // ------------------------------------------------------------------ person
  /**
   * o: kind, x, y, s, t, dir, pose (A.PP), legs ('stand'|'wide'|'jog'|'fly'), jog (phase), mood
   * ('neutral'|'scowl'|'yell'|'shock'|'slack'|'happy'|'tired'|'sad'|'wince'|'smile'|'calm'), talk, blink, look,
   * super (0..1), level (0..1 long hair), sweat (0..1), eyesClosed, alpha, rot, prop {r:'phone'|'putter'|'watch'}, outfit overrides
   */
  A.person = function (ctx, o) {
    const K = Object.assign({}, KINDS[o.kind || 'villager'], o.outfit || {});
    const s = o.s ?? 1, t = o.t || 0, outline = C(OUT);
    const skin = C(K.skin), top = C(K.top), top2 = C(K.top2), pants = C(K.pants);
    ctx.save();
    ctx.translate(o.x, o.y);
    if (o.alpha !== undefined) ctx.globalAlpha *= o.alpha;
    if (!o.noShadow && o.legs !== 'fly') { ctx.fillStyle = 'rgba(0,0,0,0.2)'; ellipse(ctx, 0, 2, 70 * s, 12 * s); ctx.fill(); }
    ctx.scale(s * (o.dir ?? 1), s);
    if (o.rot) { ctx.translate(0, -180); ctx.rotate(o.rot); ctx.translate(0, 180); }
    const legs = o.legs || 'stand';
    const jp = o.jog ?? 0;
    const bob = legs === 'jog' ? -Math.abs(Math.sin(jp)) * 10 : legs === 'wide' ? 26 : Math.sin(t * 2) * 1.5;
    const hipY = -150 + bob + (o.crouch || 0) * 30;
    const shY = hipY - 108 + (o.slump || 0) * 10;
    const hw = 30 * K.width;

    // legs (2-bone IK hip -> knee -> foot)
    const feet = {
      stand: [[-26, 0], [26, 0]], wide: [[-74, 0], [74, 0]], fly: [[-14, 30], [18, 20]],
      jog: [[-24 + Math.sin(jp) * 18, -Math.max(0, Math.sin(jp)) * 40], [24 - Math.sin(jp) * 18, -Math.max(0, -Math.sin(jp)) * 40]],
    }[legs] || [[-26, 0], [26, 0]];
    if (legs === 'fly') { feet[0] = [-16, hipY + 160]; feet[1] = [16, hipY + 150]; }
    [[-1, feet[0]], [1, feet[1]]].forEach(([side, f]) => {
      const j = ik(side * 20, hipY, f[0], f[1] - 16, 74, 66, legs === 'wide' ? -side : side * 0.4 > 0 ? -1 : 1);
      limb(ctx, side * 20, hipY, j, 34, pants, outline);
      if (K.cuff && o.kind === 'goku') { ctx.strokeStyle = C(K.shoe); ctx.lineWidth = 34; ctx.beginPath(); ctx.moveTo(j.hx - Math.cos(j.a2) * 18, j.hy - Math.sin(j.a2) * 18); ctx.lineTo(j.hx, j.hy); ctx.stroke(); }
      rrect(ctx, f[0] - 26 + side * 4, f[1] - 22, 52, 24, 10);
      ctx.fillStyle = C(K.shoe); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
      if (o.kind === 'goku') { ctx.strokeStyle = C('#d6322b'); ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(f[0] - 10 + side * 4, f[1] - 20); ctx.lineTo(f[0] - 10 + side * 4, f[1]); ctx.stroke(); }
    });

    // hair behind
    const hy = shY - 64;
    if (o.kind === 'goku') gokuHair(ctx, hy, Object.assign({ t }, o), false);

    // torso
    ctx.beginPath();
    ctx.moveTo(-hw - 4, hipY + 10);
    ctx.quadraticCurveTo(-hw - 18 - (K.belly ? 10 : 0), (hipY + shY) / 2 + 10, -hw - 12, shY + 6);
    ctx.quadraticCurveTo(0, shY - 16, hw + 12, shY + 6);
    ctx.quadraticCurveTo(hw + 18 + (K.belly ? 10 : 0), (hipY + shY) / 2 + 10, hw + 4, hipY + 10);
    ctx.closePath();
    ctx.fillStyle = top; ctx.fill();
    ctx.save(); ctx.clip();
    if (o.kind === 'goku' || o.kind === 'alien') {
      ctx.fillStyle = C(K.under);
      ctx.beginPath(); ctx.moveTo(-26, shY - 6); ctx.lineTo(0, shY + 46); ctx.lineTo(26, shY - 6); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = top2; ctx.lineWidth = 6;
      ctx.beginPath(); ctx.moveTo(-26, shY - 6); ctx.lineTo(4, shY + 50); ctx.stroke();
      ctx.fillStyle = C(K.belt); ctx.fillRect(-hw - 30, hipY - 18, 2 * hw + 60, 22);
    } else if (o.kind === 'chad') {
      rrect(ctx, -34, hipY - 52, 68, 40, 10); ctx.fillStyle = top2; ctx.fill(); ctx.strokeStyle = C(OUT); ctx.lineWidth = 3; ctx.stroke();
      ctx.strokeStyle = '#f4f4f4'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(-12, shY + 6); ctx.lineTo(-14, shY + 54); ctx.moveTo(12, shY + 6); ctx.lineTo(14, shY + 50); ctx.stroke();
      ctx.fillStyle = top2; ctx.fillRect(-hw - 30, hipY - 6, 2 * hw + 60, 16);
    } else {
      ctx.fillStyle = top2; ctx.fillRect(-hw - 30, hipY - 14, 2 * hw + 60, 14);
    }
    ctx.restore();
    ctx.strokeStyle = outline; ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.moveTo(-hw - 4, hipY + 10);
    ctx.quadraticCurveTo(-hw - 18 - (K.belly ? 10 : 0), (hipY + shY) / 2 + 10, -hw - 12, shY + 6);
    ctx.quadraticCurveTo(0, shY - 16, hw + 12, shY + 6);
    ctx.quadraticCurveTo(hw + 18 + (K.belly ? 10 : 0), (hipY + shY) / 2 + 10, hw + 4, hipY + 10);
    ctx.closePath(); ctx.stroke();
    if (o.kind === 'chad') { // bunched hood behind the neck
      ellipse(ctx, 0, shY - 2, 40, 14); ctx.fillStyle = top2; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
    }

    // arms
    const pose = o.pose || A.PP.idle;
    const lift = shY - (-258);
    const arm = (side) => {
      const sx = side === 'r' ? hw + 10 : -hw - 10, sy = shY + 14;
      const tgt = pose[side];
      const j = ik(sx, sy, tgt[0], tgt[1] + lift * 0.9, 74, 70, side === 'r' ? pose.rb : pose.lb);
      limb(ctx, sx, sy, j, 26, top, outline);
      if (o.kind === 'goku' || o.kind === 'alien') {
        ctx.strokeStyle = C(K.cuff); ctx.lineWidth = 26;
        ctx.beginPath(); ctx.moveTo(j.hx - Math.cos(j.a2) * 22, j.hy - Math.sin(j.a2) * 22); ctx.lineTo(j.hx - Math.cos(j.a2) * 8, j.hy - Math.sin(j.a2) * 8); ctx.stroke();
      }
      const prop = o.prop && o.prop[side];
      if (prop === 'putter') {
        ctx.save(); ctx.translate(j.hx, j.hy); ctx.rotate(0.12);
        ctx.strokeStyle = outline; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(0, -10); ctx.lineTo(0, 150); ctx.stroke();
        ctx.strokeStyle = C('#c0c6cc'); ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(0, -10); ctx.lineTo(0, 150); ctx.stroke();
        rrect(ctx, -6, 146, 34, 12, 3); ctx.fillStyle = C('#9aa2aa'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 3; ctx.stroke();
        ctx.restore();
      }
      circle(ctx, j.hx, j.hy, pose.fists ? 19 : 16); ctx.fillStyle = outline; ctx.fill();
      circle(ctx, j.hx, j.hy, pose.fists ? 15 : 12); ctx.fillStyle = skin; ctx.fill();
      if (prop === 'phone') { rrect(ctx, j.hx - 8, j.hy - 30, 18, 34, 4); ctx.fillStyle = C('#22262e'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 3; ctx.stroke(); }
      if (prop === 'watch') { circle(ctx, j.hx - 18, j.hy + 4, 9); ctx.fillStyle = '#eaf6ff'; ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 3; ctx.stroke(); }
      return j;
    };
    if (pose.cross) { arm('l'); } else { arm('l'); arm('r'); }

    // head
    ctx.save();
    ctx.translate(0, hy + 40);
    ctx.rotate(o.headTilt || 0);
    ctx.translate(0, -(hy + 40));
    rrect(ctx, -15, hy + 30, 30, 30, 8); ctx.fillStyle = skin; ctx.fill();
    for (const sx of [-1, 1]) { circle(ctx, sx * 41, hy + 6, 13); ctx.fillStyle = outline; ctx.fill(); circle(ctx, sx * 41, hy + 6, 9); ctx.fillStyle = skin; ctx.fill(); }
    const jaw = o.mood === 'slack' ? 10 : 0;
    ellipse(ctx, 0, hy + jaw / 2, 45, 51 + jaw / 2); ctx.fillStyle = outline; ctx.fill();
    ellipse(ctx, 0, hy + jaw / 2, 40, 46 + jaw / 2); ctx.fillStyle = skin; ctx.fill();
    if (o.kind === 'alien') { for (const sx of [-1, 1]) { ctx.fillStyle = C('#3f7f9e'); ctx.beginPath(); ctx.moveTo(sx * 18, hy - 40); ctx.lineTo(sx * 28, hy - 66); ctx.lineTo(sx * 32, hy - 38); ctx.fill(); } }
    if (o.kind === 'chad') { ctx.fillStyle = 'rgba(90,60,40,0.25)'; ellipse(ctx, 0, hy + 26 + jaw, 30, 18); ctx.fill(); }
    if (o.sweat > 0 || o.mood === 'tired') { ctx.fillStyle = 'rgba(230,100,100,0.3)'; ellipse(ctx, -24, hy + 12, 10, 6); ctx.fill(); ellipse(ctx, 24, hy + 12, 10, 6); ctx.fill(); }

    const mood = o.mood || 'neutral';
    const look = o.look || { x: 0, y: 0 };
    const sup = o.super || 0;
    for (const sx of [-1, 1]) {
      const ex = sx * 16 + look.x * 3, ey = hy - 4 + look.y * 2;
      if (o.eyesClosed || o.blink || mood === 'happy' && o.kind !== 'goku') {
        ctx.strokeStyle = '#2a1a12'; ctx.lineWidth = 4; ctx.lineCap = 'round';
        ctx.beginPath();
        if (o.eyesClosed && (mood === 'yell')) { ctx.moveTo(ex - 9, ey - 2); ctx.lineTo(ex + 9, ey + 2 * sx); }
        else ctx.arc(ex, ey + (mood === 'happy' ? 4 : 0), 7, Math.PI * (mood === 'happy' ? 1.15 : 0.15), Math.PI * (mood === 'happy' ? 1.85 : 0.85));
        ctx.stroke();
      } else if (o.kind === 'goku' || o.kind === 'alien') {
        const big = mood === 'shock' || mood === 'slack' ? 1.25 : 1;
        ctx.beginPath(); ctx.ellipse(ex, ey, 11 * big, 8 * big, sx * 0.12, 0, TAU); ctx.fillStyle = '#fff'; ctx.fill();
        ctx.strokeStyle = '#2a1a12'; ctx.lineWidth = 3; ctx.stroke();
        circle(ctx, ex + look.x * 2 - sx * 1, ey, mood === 'shock' || mood === 'slack' ? 2.6 : 4.2); ctx.fillStyle = sup > 0.5 ? '#1f9c8e' : '#1a1210'; ctx.fill();
      } else {
        const big = mood === 'shock' ? 1.5 : 1;
        ellipse(ctx, ex, ey, 5.5 * big, 7.5 * big); ctx.fillStyle = '#2a1a12'; ctx.fill();
        circle(ctx, ex + 1.5, ey - 2.5, 1.8); ctx.fillStyle = '#fff'; ctx.fill();
      }
    }
    // brows
    const bk = { scowl: 1.2, yell: 1.4, shock: -1, slack: -1.2, sad: -1, tired: -0.6, wince: -0.8, happy: -0.3, smile: -0.2, calm: -0.3, neutral: 0 }[mood] || 0;
    ctx.strokeStyle = o.kind === 'goku' ? C(mix('#1b1b22', '#e0a400', sup)) : '#4a3020';
    ctx.lineWidth = o.kind === 'goku' ? 7 : 5; ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(-30, hy - 22 - bk * 3); ctx.lineTo(-8, hy - 18 + bk * 6);
    const bu = (o.browUp || 0) * 14;
    ctx.moveTo(8, hy - 18 + bk * 6 - bu); ctx.lineTo(30, hy - 22 - bk * 3 - bu * 1.4);
    ctx.stroke();
    // nose
    ctx.strokeStyle = 'rgba(80,40,20,0.6)'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(2, hy + 2); ctx.lineTo(6, hy + 12); ctx.lineTo(0, hy + 14); ctx.stroke();
    // mouth
    const tk = clamp(o.talk || 0);
    const my = hy + 28 + jaw;
    ctx.lineCap = 'round';
    if (mood === 'yell') {
      const op = Math.max(0.7, tk);
      ctx.beginPath(); ctx.ellipse(0, my + 2, 18, 8 + op * 14, 0, 0, TAU); ctx.fillStyle = '#4a1414'; ctx.fill();
      ctx.fillStyle = '#fff'; ctx.fillRect(-14, my - 6 - op * 6, 28, 6);
    } else if (tk > 0.05) {
      ellipse(ctx, 0, my + 2, 9 + tk * 6, 2 + tk * 12); ctx.fillStyle = '#4a1414'; ctx.fill();
      ellipse(ctx, 0, my + 6 + tk * 6, 6, 1 + tk * 4); ctx.fillStyle = '#e07b84'; ctx.fill();
    } else if (mood === 'slack' || mood === 'shock') {
      ellipse(ctx, 0, my + 4, 8, 12); ctx.fillStyle = '#4a1414'; ctx.fill();
    } else if (mood === 'scowl' || mood === 'sad' || mood === 'wince') {
      ctx.strokeStyle = '#4a1414'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.arc(0, my + 12, 12, Math.PI + 0.6, TAU - 0.6); ctx.stroke();
    } else if (mood === 'flat') {
      ctx.strokeStyle = '#4a1414'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(-10, my + 2); ctx.lineTo(10, my + 2); ctx.stroke();
    } else if (mood === 'tired') {
      ellipse(ctx, 0, my + 2, 9, 6 + Math.abs(Math.sin(t * 6)) * 5); ctx.fillStyle = '#4a1414'; ctx.fill();
    } else {
      ctx.strokeStyle = '#4a1414'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.arc(0, my - 8, 14, 0.5, Math.PI - 0.5); ctx.stroke();
    }
    // hair in front
    if (o.kind === 'goku') gokuHair(ctx, hy, Object.assign({ t }, o), true);
    else if (o.kind === 'chad') chadHair(ctx, hy);
    else if (o.kind === 'villager') villagerHair(ctx, hy, o);
    if (o.sweat > 0) {
      for (let i = 0; i < 3; i++) {
        const k = ((t * 0.9 + i / 3) % 1);
        ctx.globalAlpha *= 1;
        ctx.fillStyle = `rgba(150,210,255,${o.sweat * (1 - k)})`;
        const sx = i === 1 ? 46 : -50 + i * 4;
        ctx.beginPath(); ctx.moveTo(sx, hy - 20 + k * 40); ctx.quadraticCurveTo(sx - 7, hy - 4 + k * 40, sx, hy + k * 40); ctx.quadraticCurveTo(sx + 7, hy - 4 + k * 40, sx, hy - 20 + k * 40); ctx.fill();
      }
    }
    ctx.restore();
    if (pose.cross) {
      arm('r');
      // forearm of the left arm laid over the right for the crossed look
      ctx.save();
      const sx = -hw - 10, sy = shY + 14;
      const j = ik(sx, sy, 34, -204 + lift * 0.9, 74, 70, 1);
      ctx.strokeStyle = outline; ctx.lineWidth = 34; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(j.ex, j.ey); ctx.lineTo(j.hx, j.hy); ctx.stroke();
      ctx.strokeStyle = top; ctx.lineWidth = 26; ctx.beginPath(); ctx.moveTo(j.ex, j.ey); ctx.lineTo(j.hx, j.hy); ctx.stroke();
      ctx.restore();
    }
    ctx.restore();
  };

  // ------------------------------------------------------------------ FX
  A.aura = function (ctx, x, y, s, t, k, color = '#ffd23a') {
    if (k <= 0) return;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    const g = ctx.createRadialGradient(0, -200, 20, 0, -200, 340);
    g.addColorStop(0, rgba(color, 0.55 * k));
    g.addColorStop(1, rgba(color, 0));
    ctx.fillStyle = g;
    circle(ctx, 0, -200, 340); ctx.fill();
    ctx.globalCompositeOperation = 'lighter';
    for (let layer = 0; layer < 2; layer++) {
      ctx.beginPath();
      const n = 16;
      for (let i = 0; i <= n; i++) {
        const a = Math.PI + (i / n) * Math.PI;
        const rx = (150 - layer * 30) * (1 + 0.1 * Math.sin(t * 14 + i * 2.3));
        const ry = (330 - layer * 50) * (0.85 + 0.25 * Math.abs(Math.sin(t * 9 + i * 1.7)));
        const px = Math.cos(a) * rx, py = -170 + Math.sin(a) * ry;
        if (i === 0) ctx.moveTo(px, 10); else ctx.lineTo(px * (i % 2 ? 0.75 : 1), i % 2 ? -170 + Math.sin(a) * ry * 0.7 : py);
      }
      ctx.lineTo(150 - layer * 30, 10);
      ctx.quadraticCurveTo(0, 40, -150 + layer * 30, 10);
      ctx.fillStyle = rgba(layer ? '#ffffff' : color, (layer ? 0.18 : 0.32) * k);
      ctx.fill();
    }
    ctx.restore();
  };
  A.sparks = function (ctx, x, y, s, t, k) {
    if (k <= 0) return;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.strokeStyle = `rgba(190,230,255,${0.9 * k})`;
    ctx.lineWidth = 3;
    for (let i = 0; i < 4; i++) {
      if (hash(Math.floor(t * 12) + i * 7) < 0.45) continue;
      let px = (hash(i + Math.floor(t * 12)) - 0.5) * 220, py = -60 - hash(i * 3 + Math.floor(t * 12)) * 320;
      ctx.beginPath(); ctx.moveTo(px, py);
      for (let j = 0; j < 4; j++) { px += (hash(i * 9 + j + Math.floor(t * 12)) - 0.5) * 50; py += 18 + hash(j + i) * 10; ctx.lineTo(px, py); }
      ctx.stroke();
    }
    ctx.restore();
  };
  A.rocks = function (ctx, x, y, t, k, seed = 0) {
    if (k <= 0) return;
    ctx.save();
    for (let i = 0; i < 9; i++) {
      const rx = x + (hash(i + seed) - 0.5) * 900;
      const ry = y - k * (40 + hash(i * 3 + seed) * 220) + Math.sin(t * 2 + i) * 8;
      const r = 8 + hash(i * 5) * 18;
      ctx.save(); ctx.translate(rx, ry); ctx.rotate(t * (hash(i) - 0.5));
      ctx.beginPath(); ctx.moveTo(-r, 0); ctx.lineTo(-r * 0.4, -r); ctx.lineTo(r * 0.8, -r * 0.6); ctx.lineTo(r, r * 0.5); ctx.lineTo(-r * 0.2, r); ctx.closePath();
      ctx.fillStyle = C('#a0714a'); ctx.fill(); ctx.strokeStyle = C(OUT); ctx.lineWidth = 3; ctx.stroke();
      ctx.restore();
    }
    ctx.restore();
  };
  /** k: seconds since detonation */
  A.explosion = function (ctx, x, y, k, R = 300) {
    if (k < 0 || k > 4) return;
    ctx.save();
    const grow = 1 - Math.exp(-k * 5);
    const fade = clamp(1 - (k - 0.6) / 1.6);
    if (fade > 0) {
      const r = R * (0.3 + 0.9 * grow);
      const g = ctx.createRadialGradient(x, y, 0, x, y, r);
      g.addColorStop(0, `rgba(255,255,240,${fade})`);
      g.addColorStop(0.35, `rgba(255,215,90,${fade})`);
      g.addColorStop(0.7, `rgba(255,120,40,${0.9 * fade})`);
      g.addColorStop(1, 'rgba(255,80,20,0)');
      ctx.fillStyle = g; circle(ctx, x, y, r); ctx.fill();
      ctx.strokeStyle = `rgba(255,255,255,${0.6 * fade})`; ctx.lineWidth = 10;
      ellipse(ctx, x, y + R * 0.1, R * 1.6 * grow, R * 0.35 * grow); ctx.stroke();
    }
    for (let i = 0; i < 10; i++) {
      const sk = clamp((k - 0.2) / 3);
      if (sk <= 0) continue;
      const a = Math.PI + hash(i) * Math.PI;
      const sr = R * (0.4 + 0.5 * sk) * (0.6 + hash(i * 3));
      ctx.fillStyle = `rgba(70,60,60,${0.55 * (1 - sk)})`;
      circle(ctx, x + Math.cos(a) * sr * 0.8, y + Math.sin(a) * sr * 0.6 - sk * R * 0.5, R * 0.25 * (0.5 + sk));
      ctx.fill();
    }
    for (let i = 0; i < 18; i++) {
      const a = -Math.PI * (0.05 + 0.9 * hash(i * 7));
      const v = 500 + hash(i * 3) * 700;
      const px = x + Math.cos(a) * v * k, py = y + Math.sin(a) * v * k + 900 * k * k;
      if (py > y + 400) continue;
      ctx.fillStyle = C('#6b4a32');
      ctx.fillRect(px - 6, py - 6, 12, 12);
    }
    ctx.restore();
  };
  A.speedLines = function (ctx, t, k, ang = 0) {
    if (k <= 0) return;
    ctx.save();
    ctx.translate(W / 2, H / 2);
    ctx.rotate(ang);
    ctx.strokeStyle = `rgba(255,255,255,${0.6 * k})`;
    ctx.lineCap = 'round';
    for (let i = 0; i < 26; i++) {
      const y = (hash(i * 3.3) - 0.5) * H * 1.4;
      const x = ((hash(i * 5.1) * 3000 + t * 4000) % 3000) - 1500;
      ctx.lineWidth = 2 + hash(i) * 5;
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 200 - hash(i * 2) * 300, y); ctx.stroke();
    }
    ctx.restore();
  };
  A.bulb = function (ctx, x, y, s, alpha = 1) {
    if (alpha <= 0) return;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.globalAlpha *= alpha;
    const g = ctx.createRadialGradient(0, -10, 4, 0, -10, 70);
    g.addColorStop(0, 'rgba(255,240,150,0.8)'); g.addColorStop(1, 'rgba(255,240,150,0)');
    ctx.fillStyle = g; circle(ctx, 0, -10, 70); ctx.fill();
    circle(ctx, 0, -14, 22); ctx.fillStyle = '#fff3a6'; ctx.fill(); ctx.strokeStyle = OUT; ctx.lineWidth = 4; ctx.stroke();
    rrect(ctx, -10, 6, 20, 16, 4); ctx.fillStyle = '#b9c2c9'; ctx.fill(); ctx.stroke();
    ctx.strokeStyle = '#ffd23a'; ctx.lineWidth = 4;
    for (let i = 0; i < 6; i++) { const a = -Math.PI / 2 + (i - 2.5) * 0.45; ctx.beginPath(); ctx.moveTo(Math.cos(a) * 32, -14 + Math.sin(a) * 32); ctx.lineTo(Math.cos(a) * 44, -14 + Math.sin(a) * 44); ctx.stroke(); }
    ctx.restore();
  };
  A.heartCrack = function (ctx, x, y, s, k) {
    if (k <= 0) return;
    A.heart(ctx, x, y, s, clamp(k * 2));
    ctx.save();
    ctx.translate(x, y); ctx.scale(s, s);
    ctx.globalAlpha *= clamp(k * 2);
    ctx.strokeStyle = OUT; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(0, -18); ctx.lineTo(-4, -8); ctx.lineTo(4, -2); ctx.lineTo(-2, 6); ctx.stroke();
    ctx.restore();
  };

  // ------------------------------------------------------------------ sets
  A.CPAL = {
    canyon: { skyTop: '#5aa8e6', skyBot: '#fbe3b0', far: '#d9a873', far2: '#c48a5a', mid: '#b5703f', ground: '#d8a467', ground2: '#c08a52', tint: '#000000', tk: 0, sun: '#fff4c8' },
    canyonGold: { skyTop: '#d46a4a', skyBot: '#ffd18a', far: '#c07a5a', far2: '#a8604a', mid: '#8a4a32', ground: '#c08452', ground2: '#a86e42', tint: '#ff9a5a', tk: 0.12, sun: '#ffe2a0' },
    canyonStorm: { skyTop: '#3a3f5a', skyBot: '#a88a7a', far: '#8a6a5a', far2: '#7a5a4a', mid: '#6a4a3a', ground: '#9a7452', ground2: '#866244', tint: '#2a2240', tk: 0.25, sun: '#ffe2a0' },
    village: { skyTop: '#62b6f0', skyBot: '#dff3ff', far: '#a3d395', far2: '#86c278', mid: '#79bd68', ground: '#79bd68', ground2: '#5ea24f', tint: '#000000', tk: 0, sun: '#fff4b8' },
    dusk: { skyTop: '#2e2a5e', skyBot: '#f2906a', far: '#6a5a86', far2: '#5a4a76', mid: '#4a5f4a', ground: '#4f6a44', ground2: '#405a38', tint: '#3a2a5a', tk: 0.32, sun: '#ffc07a' },
  };
  function mesaPath(ctx, x, base, w, h, seed) {
    ctx.beginPath();
    ctx.moveTo(x - w / 2 - 40, base);
    ctx.lineTo(x - w / 2, base - h * 0.9);
    ctx.lineTo(x - w / 2 + 20, base - h);
    ctx.lineTo(x + w / 2 - 10, base - h - hash(seed) * 10);
    ctx.lineTo(x + w / 2 + 10, base - h * 0.85);
    ctx.lineTo(x + w / 2 + 40, base);
    ctx.closePath();
  }
  /** canyon set. o.peaks: [{x, gone(0..1), rubble}], o.cracks, o.sunY */
  A.canyon = function (ctx, t, cam, pal, o = {}) {
    A.sky(ctx, pal);
    A.sun(ctx, o.sunX ?? 1500, o.sunY ?? 180, 60, pal.sun, 0.8);
    if (o.clouds !== false) A.clouds(ctx, t, Object.assign({ cloud: '#fff8ee' }, pal), cam, 0.7);
    ctx.save(); applyCam(ctx, cam, 0.3);
    for (let i = 0; i < 9; i++) {
      const x = -800 + i * 420 + hash(i) * 120;
      mesaPath(ctx, x, 700, 260 + hash(i * 3) * 160, 140 + hash(i * 5) * 120, i);
      ctx.fillStyle = mix(pal.far, '#ffffff', 0.15); ctx.fill();
    }
    ctx.restore();
    ctx.save(); applyCam(ctx, cam, 0.6);
    for (let i = 0; i < 7; i++) {
      const x = -600 + i * 520 + hash(i * 9) * 200;
      mesaPath(ctx, x, 780, 200 + hash(i * 2) * 140, 220 + hash(i * 4) * 160, i + 30);
      ctx.fillStyle = pal.far2; ctx.fill();
      ctx.strokeStyle = mix(pal.far2, '#000000', 0.15); ctx.lineWidth = 4;
      for (let k = 1; k < 4; k++) { ctx.beginPath(); ctx.moveTo(x - 100, 780 - k * 55); ctx.lineTo(x + 100, 780 - k * 55 - 6); ctx.stroke(); }
    }
    ctx.restore();
    ctx.save(); applyCam(ctx, cam, 1);
    // exploding peaks
    for (const p of o.peaks || []) {
      const gone = clamp(p.gone || 0);
      if (gone < 1) {
        ctx.save();
        ctx.translate(p.x, 800);
        ctx.scale(1, 1 - gone * 0.8);
        ctx.beginPath();
        ctx.moveTo(-320, 0); ctx.lineTo(-180, -260); ctx.lineTo(-90, -330); ctx.lineTo(-20, -520); ctx.lineTo(60, -410); ctx.lineTo(140, -460); ctx.lineTo(220, -240); ctx.lineTo(330, 0);
        ctx.closePath();
        ctx.fillStyle = C(pal.mid); ctx.fill(); ctx.strokeStyle = C(OUT); ctx.lineWidth = 6; ctx.lineJoin = 'round'; ctx.stroke();
        ctx.fillStyle = C(mix(pal.mid, '#000000', 0.18));
        ctx.beginPath(); ctx.moveTo(-20, -520); ctx.lineTo(60, -410); ctx.lineTo(10, -200); ctx.lineTo(-60, 0); ctx.lineTo(-90, -330); ctx.closePath(); ctx.fill();
        ctx.restore();
      }
      if (gone > 0) {
        ctx.fillStyle = C(mix(pal.mid, '#000000', 0.25));
        ctx.beginPath(); ctx.moveTo(p.x - 360, 800);
        for (let i = 0; i <= 12; i++) ctx.lineTo(p.x - 360 + i * 60, 800 - 40 - hash(i + p.x) * 90 * gone);
        ctx.lineTo(p.x + 360, 800); ctx.closePath(); ctx.fill();
        ctx.strokeStyle = C(OUT); ctx.lineWidth = 5; ctx.stroke();
      }
    }
    // ground
    const g = ctx.createLinearGradient(0, 760, 0, 1400);
    g.addColorStop(0, C(pal.ground)); g.addColorStop(1, C(pal.ground2));
    ctx.fillStyle = g;
    ctx.fillRect(-2000, 790, 6000, 1600);
    ctx.strokeStyle = C(mix(pal.ground, '#000000', 0.2)); ctx.lineWidth = 3;
    for (let i = 0; i < 40; i++) {
      const x = -1200 + hash(i * 1.7) * 4200, y = 830 + hash(i * 3.1) * 380;
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 30, y + 4); ctx.lineTo(x + 50, y - 2); ctx.stroke();
    }
    for (let i = 0; i < 26; i++) {
      const x = -1200 + hash(i * 7.7) * 4200, y = 820 + hash(i * 5.3) * 380;
      ctx.fillStyle = C(mix(pal.ground, '#000000', 0.12)); ellipse(ctx, x, y, 14 + hash(i) * 10, 8); ctx.fill();
    }
    if (o.crater) { ctx.fillStyle = C(mix(pal.ground, '#000000', 0.3)); ellipse(ctx, o.crater[0], o.crater[1], 220, 40); ctx.fill(); }
    ctx.restore();
  };

  function dome(ctx, x, base, w, h, roof, seed) {
    const outline = C(OUT);
    ctx.save(); ctx.translate(x, base);
    ctx.beginPath(); ctx.moveTo(-w / 2, 0); ctx.lineTo(-w / 2, -h * 0.35); ctx.bezierCurveTo(-w / 2, -h * 1.15, w / 2, -h * 1.15, w / 2, -h * 0.35); ctx.lineTo(w / 2, 0); ctx.closePath();
    ctx.fillStyle = C('#f6f1e6'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 5; ctx.stroke();
    ctx.save(); ctx.clip();
    ctx.fillStyle = C(roof); ctx.fillRect(-w / 2, -h * 0.62, w, 20);
    ctx.restore();
    rrect(ctx, -24, -96, 48, 96, [24, 24, 0, 0]); ctx.fillStyle = C('#6b8fb0'); ctx.fill(); ctx.strokeStyle = outline; ctx.lineWidth = 4; ctx.stroke();
    for (const sx of [-1, 1]) { circle(ctx, sx * w * 0.3, -h * 0.42, 18); ctx.fillStyle = C('#9fd4f2'); ctx.fill(); ctx.strokeStyle = outline; ctx.stroke(); }
    ctx.restore();
  }
  /** village set. o.golf: draw the mini-golf hole in the foreground; o.flashes: horizon flicker 0..1 */
  A.village = function (ctx, t, cam, pal, o = {}) {
    A.sky(ctx, pal);
    if (pal.tk > 0.2) A.stars(ctx, t, 0.4);
    A.sun(ctx, o.sunX ?? 1450, o.sunY ?? 180, 58, pal.sun, 0.8);
    if (o.flashes > 0) {
      ctx.save(); applyCam(ctx, cam, 0.25);
      const g = ctx.createRadialGradient(o.flashX ?? 1500, 640, 10, o.flashX ?? 1500, 640, 500);
      g.addColorStop(0, `rgba(255,240,180,${0.8 * o.flashes})`); g.addColorStop(1, 'rgba(255,200,120,0)');
      ctx.fillStyle = g; ctx.fillRect(-1000, -500, 4000, 2000);
      ctx.restore();
    }
    A.clouds(ctx, t, Object.assign({ cloud: pal.tk > 0.2 ? '#7a6a9a' : '#ffffff' }, pal), cam, 0.8);
    ctx.save(); applyCam(ctx, cam, 0.35);
    ctx.fillStyle = pal.far;
    ctx.beginPath(); ctx.moveTo(-1500, 1400);
    for (let x = -1500; x <= 3500; x += 20) ctx.lineTo(x, 640 - 50 * Math.sin(x * 0.003 + 1) - 25 * Math.sin(x * 0.011));
    ctx.lineTo(3500, 1400); ctx.fill();
    // the canyon mesas far away on the right, where Goku is
    for (let i = 0; i < 4; i++) { mesaPath(ctx, 2000 + i * 260, 640, 180, 90 + i * 20, i); ctx.fillStyle = mix(pal.far, '#c48a5a', 0.6); ctx.fill(); }
    if (o.far) o.far(ctx);
    ctx.restore();
    ctx.save(); applyCam(ctx, cam, 0.6);
    ctx.fillStyle = pal.far2;
    ctx.beginPath(); ctx.moveTo(-1500, 1400);
    for (let x = -1500; x <= 3500; x += 20) ctx.lineTo(x, 720 - 30 * Math.sin(x * 0.005 + 2));
    ctx.lineTo(3500, 1400); ctx.fill();
    for (let i = 0; i < 14; i++) { const x = -900 + i * 320 + hash(i) * 100; ctx.fillStyle = mix(pal.far2, '#000000', 0.15); circle(ctx, x, 700 - 30 * Math.sin(x * 0.005 + 2), 34); ctx.fill(); }
    ctx.restore();
    A.ground(ctx, Object.assign({}, pal), cam);
    ctx.save(); applyCam(ctx, cam, 1);
    dome(ctx, 180, 800, 300, 260, '#d6453a', 1);
    dome(ctx, 560, 800, 240, 210, '#3a6fd6', 2);
    dome(ctx, 1380, 800, 260, 230, '#3fae5a', 3);
    dome(ctx, 1760, 800, 320, 280, '#e9a23a', 4);
    A.tree(ctx, 980, 806, 0.9);
    A.tree(ctx, -160, 806, 1.1);
    // path
    ctx.fillStyle = C('#d9c49a');
    ctx.beginPath(); ctx.moveTo(820, 1300); ctx.quadraticCurveTo(900, 900, 1060, 806); ctx.lineTo(1120, 806); ctx.quadraticCurveTo(1000, 900, 1020, 1300); ctx.fill();
    if (o.bench) {
      rrect(ctx, o.bench - 110, 880, 220, 22, 6); ctx.fillStyle = C('#9a6a3a'); ctx.fill(); ctx.strokeStyle = C(OUT); ctx.lineWidth = 4; ctx.stroke();
      for (const lx of [-90, 90]) { rrect(ctx, o.bench + lx - 8, 900, 16, 50, 3); ctx.fillStyle = C('#7a5028'); ctx.fill(); ctx.stroke(); }
    }
    if (o.golf) {
      const gx = o.golf;
      ctx.fillStyle = C('#3fae5a');
      rrect(ctx, gx - 420, 900, 840, 220, 30); ctx.fill(); ctx.strokeStyle = C('#e8e2d0'); ctx.lineWidth = 14; ctx.stroke();
      ctx.strokeStyle = C(OUT); ctx.lineWidth = 4; rrect(ctx, gx - 427, 893, 854, 234, 34); ctx.stroke();
      ellipse(ctx, gx + 300, 1010, 18, 8); ctx.fillStyle = '#1b1210'; ctx.fill();
      ctx.strokeStyle = C(OUT); ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(gx + 300, 1008); ctx.lineTo(gx + 300, 880); ctx.stroke();
      ctx.fillStyle = C('#e0473a'); ctx.beginPath(); ctx.moveTo(gx + 300, 880); ctx.lineTo(gx + 350, 895); ctx.lineTo(gx + 300, 910); ctx.fill();
      // windmill obstacle
      ctx.save(); ctx.translate(gx - 30, 960);
      rrect(ctx, -46, -130, 92, 130, 6); ctx.fillStyle = C('#d6453a'); ctx.fill(); ctx.strokeStyle = C(OUT); ctx.lineWidth = 4; ctx.stroke();
      ctx.beginPath(); ctx.moveTo(-56, -130); ctx.lineTo(0, -180); ctx.lineTo(56, -130); ctx.closePath(); ctx.fillStyle = C('#8a2e24'); ctx.fill(); ctx.stroke();
      ctx.translate(0, -140); ctx.rotate(t * 1.4 + (o.windShake || 0) * Math.sin(t * 60));
      for (let i = 0; i < 4; i++) { ctx.rotate(Math.PI / 2); rrect(ctx, -9, -110, 18, 100, 4); ctx.fillStyle = C('#f6f1e6'); ctx.fill(); ctx.stroke(); }
      ctx.restore();
    }
    ctx.restore();
  };
})();
