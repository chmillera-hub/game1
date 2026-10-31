/* Packet Loss · scenes.js
   The script, the routing data, and every scene's drawing.
   Main visuals are drawn in a 1000×680 local space; side panels in 674×680 (tall)
   or 780×340 (wide, used on phones). The engine fits both into the stage. */
(function () {
  'use strict';
  const X = window.PL;
  const {
    clamp, lerp, E, seg, fadeIO, rng, quad, P, L, rgba, ctx, txt, measure, para, rich, rr, box, ln, dot, ring,
    arrowHead, quadPath, polyPath, cross, person, packet, cellPos, cell, cellColor, stamp, gatesRow, gatesGrid, binIcon, withLocal,
  } = X;

  const land = () => X.orient() === 'land';
  const MAIN = (fn) => withLocal(L.main, 1000, 680, (s) => {
    ctx.save();
    ctx.beginPath();
    ctx.rect(-40, -12, 1080, 712);
    ctx.clip();
    fn(s);
    ctx.restore();
  });
  function SIDE(tall, wide) {
    if (L.sideMode === 'tall') withLocal(L.side, 674, 680, tall);
    else withLocal(L.side, 780, 340, wide || tall);
  }
  const YOU = [90, 420];
  const you = (o) => person(YOU[0], YOU[1], 1, Object.assign({ label: 'YOU' }, o || {}));
  const appear = (t) => seg(t, 0, 0.4, E.lin);
  function travel(t, a, b, to, w0 = 70, w1 = 150, from = [152, 326]) {
    const p = seg(t, a, b);
    return { x: lerp(from[0], to[0], p), y: lerp(from[1], to[1], p) - Math.sin(p * Math.PI) * 46, w: lerp(w0, w1, p), p };
  }
  const card = (w, h) => box(0, 0, w, h, { r: 18, fill: rgba(P.raise, 0.92), stroke: P.rule, lw: 2 });
  const eyebrow = (s, x, y, o) => txt(s, x, y, Object.assign({ fam: 'mono', size: 19, wt: 700, color: P.dim, track: 3 }, o || {}));
  const pad2 = (n) => String(n).padStart(2, '0');
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  /* ================= where a packet can end up ================= */
  const BINS = {
    inward: { name: 'INWARD', desc: 'turned back on you', tone: 'dead' },
    sealed: { name: 'SEALED', desc: 'locked in a private record', tone: 'dead' },
    sold: { name: 'SOLD', desc: 'turned into revenue or data', tone: 'dead' },
    bent: { name: 'BENT', desc: 'reached power, distorted', tone: 'dead' },
    unsent: { name: 'UNSENT', desc: 'never allowed to leave', tone: 'dead' },
    sideways: { name: 'SIDEWAYS', desc: 'reached people in the same spot', tone: 'warm' },
    delivered: { name: 'DELIVERED', desc: 'passed all four tests', tone: 'yes' },
  };
  const BIN_ORDER = ['inward', 'sealed', 'sold', 'bent', 'unsent', 'sideways', 'delivered'];
  const binColor = (k) => P[BINS[k].tone];

  /* ================= the thirteen standard routes ================= */
  const HOPS = [
    {
      id: 'gym', title: '“Go to the gym.”', route: 'go to the gym', name: 'gym', host: 'gym.local', reply: '* * *',
      bin: 'inward', status: 'ABSORBED', gates: [0, 0, 0, 0], where: 'Into your muscles. The gym receives a fee.',
      report: [['RECEIVER', 'your muscles; the gym gets a fee'], ['HUMANS INFORMED', '0'], ['POWER REACHED', 'none'], ['FIELDS FORWARDED', '0 of 8'], ['BECOMES', 'endurance']],
      beats: [
        'The signal goes into your muscles. Nobody learns that you’re lonely, overworked, or struggling to pay rent.',
        'The only party receiving anything is the gym, as a membership fee. Conditions are unchanged; your body is just better able to endure them.',
      ],
      draw: chGym,
    },
    {
      id: 'therapy', title: '“Have you tried therapy?”', route: 'try therapy', name: 'therapy', host: 'therapist.private', reply: '* * *',
      bin: 'sealed', status: 'SEALED', gates: [1, 1, 0, 0], where: 'Into a confidential file.',
      report: [['RECEIVER', 'one professional'], ['HUMANS INFORMED', '1'], ['POWER REACHED', 'none'], ['FIELDS FORWARDED', '0 of 8'], ['BECOMES', 'a confidential file']],
      beats: [
        'You say true and often devastating things about your life, and they go into a confidential file.',
        'The privacy has a real purpose. People need a place where it’s safe to speak. But structurally, the signal is sealed.',
        'A therapist might hear the same story of isolation, overwork and an exploitative employer from fifty clients. That pattern reaches no one who could change it.',
      ],
      draw: chTherapy,
    },
    {
      id: 'journal', title: '“Try journaling.”', route: 'journal about it', name: 'journaling', host: 'localhost (127.0.0.1)', reply: '* * *',
      bin: 'inward', status: 'LOOPBACK', gates: [0, 1, 0, 0], where: 'Back to you. You’re the only reader.',
      report: [['RECEIVER', 'you'], ['HUMANS INFORMED', '0 besides you'], ['POWER REACHED', 'none'], ['FIELDS FORWARDED', '0 of 8'], ['BECOMES', 'a private record']],
      beats: [
        'The signal is written down, and you’re the only reader.',
        'In network terms, it’s addressed to 127.0.0.1, the address a computer uses to talk to itself. It may help you understand yourself. It has nowhere to go.',
      ],
      draw: chJournal,
    },
    {
      id: 'meditate', title: '“Meditate. Breathe. Be mindful.”', route: 'meditate, breathe', name: 'meditation', host: 'nervous-system.local', reply: '* * *',
      bin: 'inward', status: 'MUTED', gates: [0, 0, 0, 0], where: 'Turned down at the source.',
      report: [['RECEIVER', 'your nervous system'], ['HUMANS INFORMED', '0'], ['POWER REACHED', 'none'], ['FIELDS FORWARDED', '0 of 8'], ['BECOMES', 'a quieter alarm']],
      beats: [
        'These change how strongly you react to the conditions. They don’t change the conditions.',
        'The signal gets turned down at the source. It’s an internal volume knob on the alarm.',
      ],
      draw: chMeditate,
    },
    {
      id: 'hobby', title: '“Get a hobby.”', route: 'get a hobby', name: 'hobby', host: 'hobby.local', reply: '* * *',
      bin: 'inward', status: 'DIVERTED', gates: [0, 0, 0, 0], where: 'Spent on an activity. The room never hears it.',
      report: [['RECEIVER', 'an activity'], ['HUMANS INFORMED', '0, with 3 in the room'], ['POWER REACHED', 'none'], ['FIELDS FORWARDED', '0 of 8'], ['BECOMES', 'spent energy']],
      beats: [
        'The signal is redirected into an activity. You spend the loneliness on knitting, climbing or board games.',
        'There are people in the room, but the room learns nothing about the loneliness, because talking about it would break the hobby frame.',
      ],
      draw: chHobby,
    },
    {
      id: 'selfcare', title: '“Treat yourself.”', route: 'treat yourself', name: 'self-care', host: 'checkout.retail', reply: '* * *',
      bin: 'sold', status: 'SOLD', gates: [1, 0, 0, 0], where: 'Into a retailer’s sales data.',
      report: [['RECEIVER', 'a retailer'], ['HUMANS INFORMED', '0'], ['POWER REACHED', 'none over your conditions'], ['FIELDS FORWARDED', '1 sales record'], ['BECOMES', 'market research']],
      beats: [
        'Take a bath. Buy the candle. The signal turns into a purchase.',
        'The only party that learns anything is a retailer, as sales data: sad people buy candles. Your suffering becomes market research for selling you more candles.',
      ],
      draw: chSelfCare,
    },
    {
      id: 'gratitude', title: '“Practice gratitude.”', route: 'practice gratitude', name: 'gratitude', host: 'rewrite.local', reply: '* * *',
      bin: 'inward', status: 'OVERWRITTEN', gates: [0, 0, 0, 0], where: 'Rewritten before it leaves.',
      report: [['RECEIVER', 'no one'], ['HUMANS INFORMED', '0'], ['POWER REACHED', 'none'], ['FIELDS FORWARDED', '0 of 8'], ['BECOMES', '“I’m grateful for what I have.”']],
      beats: [
        'This one doesn’t just fail to send the signal. It rewrites it.',
        '“My life lacks belonging” becomes “I’m grateful for what I have.” The complaint is deleted at the source and replaced with a message nobody needed to hear.',
      ],
      draw: chGratitude,
    },
    {
      id: 'medication', title: '“Ask about medication.”', route: 'ask about medication', name: 'medication', host: 'claims.pharmacy', reply: '* * *',
      bin: 'sealed', status: 'RECODED', gates: [1, 0, 0, 0], where: 'Into a diagnosis code and a pharmacy claim.',
      report: [['RECEIVER', 'prescriber, pharmacy, insurer'], ['HUMANS INFORMED', '1 or 2'], ['POWER REACHED', 'none over your conditions'], ['FIELDS FORWARDED', '1 diagnosis code'], ['BECOMES', 'a fact about your brain']],
      beats: [
        'Sometimes it truly helps someone survive, and that matters.',
        'Informationally, though, the signal becomes an individual diagnosis code and a pharmacy claim.',
        'In aggregate, that data counts prescriptions filled, not neighborhoods without a village. The cause gets recorded as your brain, not your conditions.',
      ],
      draw: chMedication,
    },
    {
      id: 'apps', title: '“Try the dating apps.”', route: 'try the dating apps', name: 'dating apps', host: 'match.app', reply: '* * *',
      bin: 'sold', status: 'CAPTURED', gates: [1, 1, 0, 0], where: 'To a company that profits while you stay lonely.',
      report: [['RECEIVER', 'an app company'], ['HUMANS INFORMED', '0, an algorithm'], ['POWER REACHED', 'profits if you stay lonely'], ['FIELDS FORWARDED', '8 of 8, to the company'], ['BECOMES', 'a retention metric']],
      beats: [
        'You hand over your deepest longing, and the receiver is a company that profits from your continued loneliness.',
        'The algorithm learns you. The community doesn’t. A solved user is a lost subscriber.',
      ],
      draw: chApps,
    },
    {
      id: 'selfhelp', title: '“Read this book. Try this podcast.”', route: 'read the book, try the podcast', name: 'self-help', host: 'feed.cdn', reply: '* * *',
      bin: 'sold', status: 'ONE-WAY', gates: [0, 1, 0, 0], where: 'Nowhere. The channel only flows toward you.',
      report: [['RECEIVER', 'no one: it only flows to you'], ['HUMANS INFORMED', '0'], ['POWER REACHED', 'none'], ['FIELDS FORWARDED', '0 of 8'], ['BECOMES', 'a bigger audience']],
      beats: [
        'The flow is one way. You take in their information, and they never receive yours.',
        'Millions of people absorbing the same advice don’t add up to a collective voice. They add up to a bigger audience.',
      ],
      draw: chSelfHelp,
    },
    {
      id: 'hr', title: '“Go to HR.”', route: 'go to HR', name: 'HR', host: 'hr.institution', reply: 'reached',
      bin: 'bent', status: 'LIABILITY', gates: [1, 0, 0, 1], where: 'To the institution, as liability.',
      report: [['RECEIVER', 'the institution'], ['HUMANS INFORMED', 'a few, on its side'], ['POWER REACHED', 'yes, as liability'], ['FIELDS FORWARDED', '8 of 8, relabeled'], ['BECOMES', 'a risk file']],
      beats: [
        'This one does reach power, but power receives it as liability.',
        'Your complaint lands with the department whose job is to protect the institution. It reaches power in a form that teaches power how to manage you.',
      ],
      draw: chHR,
    },
    {
      id: 'vote', title: '“Just vote.”', route: 'just vote', name: 'voting', host: 'ballot.gov', reply: '1 bit',
      bin: 'bent', status: 'COMPRESSED', gates: [1, 0, 0, 1], where: 'To government, compressed to one bit every few years.',
      report: [['RECEIVER', 'government, through a tally'], ['HUMANS INFORMED', '0 learn your conditions'], ['POWER REACHED', 'yes, as 1 bit'], ['FIELDS FORWARDED', '≤ 1 bit'], ['BECOMES', 'a checkbox']],
      beats: [
        'One of the few channels that actually reaches power. It is also extremely narrow.',
        'A choice between two options carries at most one bit. Once every four years, that’s about 0.000000008 bits per second.',
        'Your whole lived experience, compressed into a choice between options someone else picked.',
      ],
      draw: chVote,
    },
    {
      id: 'private', title: '“Keep it private.”', route: 'keep it private', name: 'keep it private', host: '“don’t make it weird”', reply: '!X',
      bin: 'unsent', status: 'DROPPED', gates: [0, 1, 0, 0], where: 'Forbidden from leaving.',
      report: [['RECEIVER', 'nobody'], ['HUMANS INFORMED', '0'], ['POWER REACHED', 'none'], ['FIELDS FORWARDED', '0 of 8'], ['BECOMES', 'silence']],
      beats: [
        '“Keep it private.” “Don’t air your dirty laundry.” “Don’t make it weird.”',
        'This one doesn’t route the signal anywhere. It forbids it outright.',
      ],
      draw: chPrivate,
    },
  ];
  HOPS.forEach((h, i) => { h.n = i + 1; h.code = 'HOP ' + pad2(i + 1); });

  /* ================= the outward channels ================= */
  const OUTS = [
    {
      id: 'truth', title: 'Tell each other the truth, in public.', name: 'tell the truth in public', bin: 'sideways', status: 'BROADCAST', gates: [1, 1, 1, 0],
      where: 'To other people, out loud.', side: 'report', draw: chTruth,
      report: [['RECEIVER', 'other people, out loud'], ['HUMANS INFORMED', '12 and counting'], ['POWER REACHED', 'not yet'], ['FIELDS FORWARDED', '8 of 8'], ['BECOMES', '“me too”']],
      beats: [
        'The channels that actually carry information outward look very different.',
        'The first is simple: people telling each other the truth about their lives, in public.',
      ],
    },
    {
      id: 'notes', title: 'Compare notes.', name: 'compare notes', bin: 'sideways', status: 'PATTERN FOUND', gates: [1, 1, 1, 0],
      where: 'Pooled with other stories until the shared part shows.', side: 'snr', draw: chNotes,
      beats: [
        'Each person’s story is the shared conditions plus their own particulars. Alone, it reads as a personal problem.',
        'Average many stories and the particulars cancel while the shared part stays. The signal-to-noise ratio grows with the square root of N.',
        'Sixteen stories make the pattern four times clearer. Two hundred fifty-six make it sixteen times clearer. The problem was never individual.',
      ],
    },
    {
      id: 'name', title: 'Name the pattern together.', name: 'name the pattern', bin: 'sideways', status: 'NAMED', gates: [1, 1, 1, 0],
      where: 'Into a shared name that can’t be waved away.', side: 'report', draw: chName, minDur: 10,
      report: [['RECEIVER', 'everyone who shares it'], ['HUMANS INFORMED', 'many witnesses'], ['POWER REACHED', 'not yet'], ['FIELDS FORWARDED', '8 of 8'], ['BECOMES', 'a pattern with a name']],
      beats: ['Naming the pattern together. Once it has a name and many witnesses, it can’t be dismissed as one person’s issue.'],
    },
    {
      id: 'organize', title: 'Organize.', name: 'organize', bin: 'delivered', status: 'DELIVERED', gates: [1, 1, 1, 1],
      where: 'Into one collective demand, delivered intact.', side: 'report', draw: chOrganize,
      report: [['RECEIVER', 'whoever controls the conditions'], ['HUMANS INFORMED', '1,000 voices'], ['POWER REACHED', 'yes, intact'], ['FIELDS FORWARDED', '8 of 8'], ['BECOMES', 'one collective demand']],
      beats: [
        'Organizing. A thousand private complaints become one collective demand, delivered intact to the people who control the conditions.',
        'It’s the first route where all four tests come back 1. That doesn’t guarantee change. It makes change possible.',
      ],
    },
    {
      id: 'aid', title: 'Practice mutual aid.', name: 'mutual aid', bin: 'delivered', status: 'MET DIRECTLY', gates: [1, 1, 1, 1],
      where: 'Straight to people who can act on it today.', side: 'report', draw: chAid,
      report: [['RECEIVER', 'each other'], ['HUMANS INFORMED', 'the whole network'], ['POWER REACHED', 'power held in common'], ['FIELDS FORWARDED', '8 of 8'], ['BECOMES', 'met needs, and a list of what’s missing']],
      beats: [
        'Mutual aid. People meet each other’s needs directly, and by doing it, they learn exactly what’s missing.',
        'The need is received by the people who can act on it today: each other.',
      ],
    },
  ];
  OUTS.forEach((o, i) => { o.n = i + 1; o.code = 'OUT ' + (i + 1); });

  /* ================= shared chamber pieces ================= */
  function meter(x, y, w, h, v, label, col) {
    box(x, y, w, h, { r: 10, stroke: P.line, lw: 2 });
    const ih = (h - 10) * clamp(v);
    if (ih > 1) box(x + 5, y + h - 5 - ih, w - 10, ih, { r: 6, fill: col });
    txt(label, x + w / 2, y + h + 36, { fam: 'mono', size: 17, color: P.dim, align: 'center', track: 2 });
  }
  function conditionsLine(y, a) {
    if (a <= 0) return;
    ctx.save();
    ctx.globalAlpha *= a;
    txt('CONDITIONS', 200, y - 18, { fam: 'mono', size: 17, color: P.dim, track: 2 });
    ln(200, y, 880, y, P.lineHi, 2.5);
    for (let x = 200; x <= 880; x += 68) ln(x, y - 7, x, y + 7, P.lineHi, 2);
    txt('× 1.00', 985, y + 10, { fam: 'mono', size: 28, wt: 800, color: P.ink, align: 'right' });
    txt('housing, wages, food, power: unchanged', 200, y + 46, { fam: 'sans', size: 24, color: P.dim });
    ctx.restore();
  }
  function scope(x, y, w, h, label, fn, col) {
    box(x, y, w, h, { r: 12, stroke: P.line, lw: 2, fill: rgba(P.raise, 0.55) });
    for (let k = 1; k < 4; k++) ln(x + 2, y + (h * k) / 4, x + w - 2, y + (h * k) / 4, P.grid, 1.2);
    txt(label, x + 22, y + 38, { fam: 'mono', size: 17, color: P.dim, track: 1.5 });
    const mid = y + h / 2 + 14;
    ctx.beginPath();
    for (let i = 0; i <= 180; i++) {
      const u = i / 180, yy = mid - fn(u);
      if (i) ctx.lineTo(x + 20 + u * (w - 40), yy); else ctx.moveTo(x + 20, yy);
    }
    ctx.strokeStyle = col;
    ctx.lineWidth = 3;
    ctx.lineJoin = 'round';
    ctx.stroke();
  }
  function bubble(x, y, s, a, o = {}) {
    if (a <= 0) return;
    ctx.save();
    ctx.globalAlpha *= clamp(a);
    const fs = o.size || 25, w = measure(s, { fam: 'sans', size: fs }) + 40, h = fs + 28, l = x - w / 2, tp = y - h / 2;
    const col = o.color || P.line, tx = x + (o.tail || 0);
    box(l, tp, w, h, { r: h / 2, fill: P.raise, stroke: col, lw: 2 });
    ctx.beginPath();
    ctx.moveTo(tx - 10, tp + h - 1);
    ctx.lineTo(tx - 4 + (o.lean || 0), tp + h + 16);
    ctx.lineTo(tx + 10, tp + h - 1);
    ctx.fillStyle = P.raise;
    ctx.fill();
    ctx.strokeStyle = col;
    ctx.lineWidth = 2;
    ctx.stroke();
    ln(tx - 8, tp + h - 1.5, tx + 8, tp + h - 1.5, P.raise, 3);
    txt(s, x, y + fs * 0.35, { fam: 'sans', size: fs, color: o.textColor || P.ink, align: 'center' });
    if (o.strike > 0) ln(l + 16, y, l + 16 + (w - 32) * o.strike, y, P.no, 3.5);
    ctx.restore();
  }
  function folder(x, y, w, h, a, closeP) {
    ctx.save();
    ctx.globalAlpha *= clamp(a);
    const l = x - w / 2, tp = y - h / 2;
    ctx.beginPath();
    ctx.moveTo(l, tp);
    ctx.lineTo(l + w * 0.36, tp);
    ctx.lineTo(l + w * 0.44, tp + 14);
    ctx.lineTo(l + w, tp + 14);
    ctx.lineTo(l + w, tp + h);
    ctx.lineTo(l, tp + h);
    ctx.closePath();
    ctx.fillStyle = rgba(P.gold, 0.14);
    ctx.fill();
    ctx.strokeStyle = P.lineHi;
    ctx.lineWidth = 2.5;
    ctx.lineJoin = 'round';
    ctx.stroke();
    const ch = lerp(h * 0.34, h - 18, E.out(clamp(closeP)));
    box(l, tp + h - ch, w, ch, { r: 4, fill: P.raise, stroke: P.lineHi, lw: 2.5 });
    ctx.restore();
  }
  function miniFile(x, y, w, h, a) {
    ctx.save();
    ctx.globalAlpha *= clamp(a);
    box(x, y + 9, w, h - 9, { r: 5, fill: P.raise, stroke: P.line, lw: 1.5 });
    box(x, y, w * 0.45, 13, { r: 3, fill: P.line });
    for (let k = 0; k < 3; k++) box(x + 8, y + 21 + k * 9, w - 24, 5, { r: 2, fill: rgba(P.warm, 0.8 - k * 0.15) });
    binIcon('sealed', x + w - 13, y + h - 13, 0.45, P.dim);
    ctx.restore();
  }
  function scribble(x, y, w, seed) {
    if (w <= 2) return;
    ctx.beginPath();
    for (let i = 0; i <= w; i += 4) {
      const yy = y + Math.sin(i * 0.35 + seed * 1.7) * 4 + Math.sin(i * 0.11 + seed) * 2;
      if (i) ctx.lineTo(x + i, yy); else ctx.moveTo(x, yy);
    }
    ctx.strokeStyle = P.warm;
    ctx.lineWidth = 2.2;
    ctx.stroke();
  }
  function yarnBall(x, y, r) {
    dot(x, y, r, rgba(P.warm, 0.16), P.warm, 2.5);
    ctx.save();
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.clip();
    for (let k = -2; k <= 2; k++) {
      ctx.beginPath();
      ctx.ellipse(x + k * r * 0.28, y, r * 0.45, r * 1.15, 0.6, 0, Math.PI * 2);
      ctx.strokeStyle = rgba(P.warm, 0.6);
      ctx.lineWidth = 1.6;
      ctx.stroke();
    }
    ctx.restore();
  }
  function gameBoard(x, y) {
    box(x - 42, y - 24, 84, 48, { r: 4, stroke: P.line, lw: 2, fill: rgba(P.raise, 0.6) });
    for (let k = 1; k < 4; k++) ln(x - 42 + k * 21, y - 24, x - 42 + k * 21, y + 24, P.rule, 1.2);
    ln(x - 42, y, x + 42, y, P.rule, 1.2);
    dot(x - 10, y - 12, 5, P.lineHi);
    dot(x + 10, y + 12, 5, P.gold);
  }
  function cartIcon(x, y) {
    ctx.beginPath();
    ctx.moveTo(x - 72, y - 52);
    ctx.lineTo(x - 54, y - 52);
    ctx.lineTo(x - 36, y + 28);
    ctx.lineTo(x + 52, y + 28);
    ctx.lineTo(x + 64, y - 30);
    ctx.lineTo(x - 47, y - 30);
    ctx.strokeStyle = P.lineHi;
    ctx.lineWidth = 3;
    ctx.lineJoin = 'round';
    ctx.stroke();
    dot(x - 24, y + 48, 9, null, P.lineHi, 3);
    dot(x + 40, y + 48, 9, null, P.lineHi, 3);
  }
  function priceTag(x, y, s, p) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(p, p);
    ctx.rotate(-0.12);
    ctx.beginPath();
    ctx.moveTo(-48, -22); ctx.lineTo(30, -22); ctx.lineTo(50, 0); ctx.lineTo(30, 22); ctx.lineTo(-48, 22);
    ctx.closePath();
    ctx.fillStyle = P.raise;
    ctx.fill();
    ctx.strokeStyle = P.gold;
    ctx.lineWidth = 2.5;
    ctx.stroke();
    dot(30, 0, 4, P.gold);
    txt(s, -9, 9, { fam: 'mono', size: 22, wt: 800, color: P.ink, align: 'center' });
    ctx.restore();
  }
  function receipt(x, y, a) {
    ctx.save();
    ctx.globalAlpha *= clamp(a);
    const w = 132, h = 176, l = x - w / 2, tp = y - h / 2;
    ctx.beginPath();
    ctx.moveTo(l, tp);
    ctx.lineTo(l + w, tp);
    ctx.lineTo(l + w, tp + h);
    for (let k = 0; k < 8; k++) ctx.lineTo(l + w - (k + 0.5) * (w / 8), tp + h + (k % 2 ? 0 : 8));
    ctx.lineTo(l, tp + h);
    ctx.closePath();
    ctx.fillStyle = P.raise;
    ctx.fill();
    ctx.strokeStyle = P.line;
    ctx.lineWidth = 2;
    ctx.stroke();
    txt('SKU 0417', x, tp + 34, { fam: 'mono', size: 14, color: P.dim, align: 'center' });
    txt('candle', x, tp + 68, { fam: 'sans', size: 24, wt: 700, color: P.ink, align: 'center' });
    txt('$24.00', x, tp + 98, { fam: 'mono', size: 17, color: P.ink, align: 'center' });
    for (let k = 0; k < 18; k++) ln(l + 20 + k * 5.4, tp + 118, l + 20 + k * 5.4, tp + 154, P.ink, k % 3 === 0 ? 3 : 1.4);
    ctx.restore();
  }
  function dashboard(x, y, w, h, t, a) {
    ctx.save();
    ctx.globalAlpha *= clamp(a);
    box(x, y, w, h, { r: 14, stroke: P.line, lw: 2, fill: rgba(P.raise, 0.92) });
    txt('CANDLE SALES', x + 22, y + 40, { fam: 'mono', size: 16, wt: 700, color: P.dim, track: 2 });
    txt('segment: sad customers', x + 22, y + 72, { fam: 'sans', size: 21, color: P.ink });
    const bars = [0.25, 0.32, 0.3, 0.46, 0.58, 0.82], g = seg(t, 3.6, 6.0, E.out);
    const bx0 = x + 26, by0 = y + h - 28, bw = (w - 52 - 5 * 12) / 6, bh = h - 132;
    ln(bx0 - 6, by0, x + w - 20, by0, P.rule, 1.5);
    bars.forEach((v, i) => {
      const hh = bh * v * g;
      if (hh > 1) box(bx0 + i * (bw + 12), by0 - hh, bw, hh, { r: 4, fill: i === 5 ? P.gold : rgba(P.line, 0.75) });
    });
    ctx.restore();
  }
  function swipeCard(cx, cy, w, h, rot, a) {
    if (a <= 0) return;
    ctx.save();
    ctx.globalAlpha *= clamp(a);
    ctx.translate(cx, cy);
    ctx.rotate(rot);
    box(-w / 2, -h / 2, w, h, { r: 12, fill: P.raise, stroke: P.line, lw: 2 });
    dot(0, -h * 0.16, w * 0.18, rgba(P.line, 0.25), P.line, 2);
    box(-w * 0.3, h * 0.12, w * 0.6, 10, { r: 5, fill: P.rule });
    box(-w * 0.2, h * 0.24, w * 0.4, 10, { r: 5, fill: P.rule });
    ctx.restore();
  }
  function checkbox(x, y, s, on, col) {
    if (s <= 0) return;
    box(x - s / 2, y - s / 2, s, s, { r: s * 0.18, stroke: col || P.ink, lw: 3, fill: P.raise });
    if (!on) return;
    ctx.beginPath();
    ctx.moveTo(x - s * 0.28, y);
    ctx.lineTo(x - s * 0.06, y + s * 0.22);
    ctx.lineTo(x + s * 0.3, y - s * 0.24);
    ctx.strokeStyle = col || P.ink;
    ctx.lineWidth = 4;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
  }
  function placard(s, x, y, rot, a) {
    if (a <= 0) return;
    ctx.save();
    ctx.globalAlpha *= clamp(a);
    ctx.translate(x, y);
    ctx.rotate(rot);
    const w = measure(s, { fam: 'sans', size: 24, wt: 700 }) + 36;
    box(-w / 2, -24, w, 48, { r: 6, fill: P.raise, stroke: P.no, lw: 2 });
    txt(s, 0, 8, { fam: 'sans', size: 24, wt: 700, color: P.ink, align: 'center' });
    ctx.restore();
  }

  /* ================= route chambers ================= */
  function chGym(t, sc) {
    const B1 = sc.B[1];
    you();
    const fx = 560, fy = 380;
    const rep = Math.sin(Math.max(0, t - 3.2) * 2.6) * 10 * seg(t, 3.2, 4.0, E.lin);
    const by = fy - 66 - rep;
    person(fx, fy, 2.0, { color: P.lineHi, fillA: 0.06 });
    const warmth = fadeIO(t, 2.4, 5.2, 0.8);
    if (warmth > 0) person(fx, fy, 2.0, { color: P.warm, fillA: 0.12, a: warmth * 0.7 });
    ln(360, by, 760, by, P.lineHi, 7);
    box(372, by - 56, 24, 112, { r: 5, fill: P.line });
    box(400, by - 40, 16, 80, { r: 4, fill: P.line });
    box(724, by - 56, 24, 112, { r: 5, fill: P.line });
    box(704, by - 40, 16, 80, { r: 4, fill: P.line });
    const tr = travel(t, 0.4, 2.4, [fx, fy + 36], 70, 150);
    const ab = seg(t, 2.4, 3.4, E.lin);
    if (ab < 1) packet(tr.x, tr.y, tr.w, { a: appear(t) * (1 - ab), glow: 0.8 });
    const sp = seg(t, 2.4, 4.2, E.lin);
    if (sp > 0 && sp < 1) {
      for (let i = 0; i < 8; i++) {
        const s0 = cellPos(fx, fy + 36, 150, i), q = E.out(sp);
        const ex = fx + (i - 3.5) * 14, ey = fy + 70 + (i % 3) * 18;
        cell(lerp(s0[0], ex, q), lerp(s0[1], ey, q), 12, 20, sp > 0.5 ? P.dead : cellColor(i), 1 - sp);
      }
    }
    meter(846, 150, 48, 320, 0.16 + 0.68 * seg(t, 2.8, 6.2), 'ENDURANCE', P.lineHi);
    box(790, 24, 196, 86, { r: 12, stroke: P.line, lw: 2, fill: rgba(P.raise, 0.85) });
    txt('THE GYM', 888, 58, { fam: 'mono', size: 17, wt: 700, color: P.dim, align: 'center', track: 2 });
    txt('a monthly fee', 888, 92, { fam: 'sans', size: 24, color: P.ink, align: 'center' });
    const cp = seg(t, B1 - 0.2, B1 + 1.4, E.io);
    if (cp > 0 && cp < 1) {
      const q = quad([120, 330], [460, -80], [888, 112], cp);
      dot(q[0], q[1], 17, P.gold);
      txt('$', q[0], q[1] + 8, { fam: 'mono', size: 20, wt: 800, color: P.raise, align: 'center' });
    }
    conditionsLine(596, seg(t, B1 + 1.6, B1 + 2.2, E.lin));
  }

  function chTherapy(t, sc) {
    const B1 = sc.B[1], B2 = sc.B[2];
    you();
    const v1 = 1 - seg(t, B2 - 0.4, B2 + 0.3, E.lin), v2 = seg(t, B2, B2 + 0.6, E.lin);
    if (v1 > 0) {
      ctx.save();
      ctx.globalAlpha *= v1;
      const c = P.line;
      ln(300, 64, 970, 64, c, 2.5); ln(970, 64, 970, 560, c, 2.5); ln(970, 560, 300, 560, c, 2.5);
      ln(300, 560, 300, 400, c, 2.5); ln(300, 290, 300, 64, c, 2.5);
      txt('SESSION · 50 MIN', 326, 104, { fam: 'mono', size: 17, color: P.dim, track: 2 });
      person(840, 400, 1.05, { color: P.lineHi, fillA: 0.06 });
      ln(790, 470, 890, 470, P.line, 3);
      ln(470, 470, 570, 470, P.line, 3);
      const tr = travel(t, 0.4, 2.4, [520, 330], 70, 130);
      const tf = seg(t, B1 - 1.3, B1 + 0.1);
      if (t > 2.4 && t < B1 - 1.0) {
        for (let k = 0; k < 3; k++) {
          const ph = ((t - 2.4) * 0.7 + k / 3) % 1;
          ctx.beginPath();
          ctx.arc(590 + ph * 160, 330, 26 + ph * 40, -0.7, 0.7);
          ctx.strokeStyle = rgba(P.warm, (1 - ph) * 0.9);
          ctx.lineWidth = 3;
          ctx.stroke();
        }
      }
      const fx = 640, fy = 470;
      const fA = seg(t, B1 - 1.8, B1 - 1.2, E.lin), fC = seg(t, B1 + 0.1, B1 + 0.7);
      if (fA > 0) folder(fx, fy, 160, 104, fA, fC);
      if (tf < 1) {
        const q = E.io(tf);
        packet(lerp(tr.x, fx, q), lerp(tr.y, fy - 10, q), lerp(tr.w, 80, q), { a: appear(t) * (tf > 0.85 ? (1 - tf) / 0.15 : 1), glow: 0.7 });
      }
      const lk = seg(t, B1 + 0.7, B1 + 1.1, E.back);
      if (lk > 0) {
        binIcon('sealed', fx + 66, fy - 48, 1.4 * lk, P.ink);
        txt('CONFIDENTIAL', fx, fy + 80, { fam: 'mono', size: 17, wt: 700, color: P.dim, align: 'center', track: 3, a: lk });
      }
      const bits = Math.round(117000 * seg(t, 2.4, B1 + 0.2, E.lin));
      txt('IN', 690, 112, { fam: 'mono', size: 17, color: P.dim, track: 2 });
      txt(bits.toLocaleString('en-US') + ' bits', 950, 112, { fam: 'mono', size: 22, wt: 700, color: P.warm, align: 'right' });
      txt('OUT', 690, 150, { fam: 'mono', size: 17, color: P.dim, track: 2 });
      txt('0 bits', 950, 150, { fam: 'mono', size: 22, wt: 700, color: P.no, align: 'right' });
      txt('speech: up to ~39 bits/s for 50 min', 950, 182, { fam: 'sans', size: 18, color: P.faint, align: 'right' });
      const pv = seg(t, B1 + 1.6, B1 + 2.2, E.lin);
      if (pv > 0) txt('a safe place to speak', 330, 530, { fam: 'sans', size: 24, color: P.yes, a: pv });
      ctx.restore();
    }
    if (v2 > 0) {
      ctx.save();
      ctx.globalAlpha *= v2;
      for (let k = 0; k < 50; k++) {
        const cc = k % 10, row = (k / 10) | 0, a = seg(t, B2 + 0.3 + k * 0.03, B2 + 0.6 + k * 0.03, E.lin);
        if (a > 0) miniFile(300 + cc * 67, 64 + row * 74, 56, 62, a);
      }
      txt('50 CLIENTS · 50 SEALED FILES', 300, 466, { fam: 'mono', size: 19, wt: 700, color: P.ink, track: 2 });
      txt('the same fields in each: isolation, overwork, an exploitative employer', 300, 502, { fam: 'sans', size: 23, color: P.dim, maxW: 670, min: 16 });
      const ip = seg(t, B2 + 2.4, B2 + 3.0, E.lin);
      if (ip > 0) {
        ln(300, 560, 960, 560, rgba(P.line, ip), 2, [6, 8]);
        const ph = ((t - B2 - 2.4) * 0.3) % 1;
        cell(lerp(300, 960, ph), 560, 16, 16, P.dead, ip);
        txt('billed to insurance: one diagnosis code, one session code', 300, 600, { fam: 'sans', size: 22, color: P.dim, a: ip, maxW: 670, min: 16 });
      }
      const nv = seg(t, B2 + 4.2, B2 + 4.8, E.lin);
      if (nv > 0) txt('PATTERN VISIBLE OUTSIDE THE ROOM: NONE', 300, 648, { fam: 'mono', size: 18, wt: 700, color: P.no, track: 1.5, a: nv, maxW: 670 });
      ctx.restore();
    }
  }

  function chJournal(t, sc) {
    const B1 = sc.B[1];
    you();
    const nx = 610, ny = 110, nw = 300, nh = 400;
    box(nx, ny, nw, nh, { r: 14, stroke: P.lineHi, lw: 2.5, fill: rgba(P.raise, 0.85) });
    for (let k = 0; k < 8; k++) ln(nx + 34, ny + 70 + k * 42, nx + nw - 26, ny + 70 + k * 42, P.rule, 1.5);
    for (let k = 0; k < 9; k++) dot(nx, ny + 28 + k * 43, 8, P.bg, P.line, 2);
    const wp = seg(t, 3.6, 6.6, E.lin);
    for (let k = 0; k < 8; k++) {
      const lp = clamp(wp * 8 - k);
      if (lp <= 0) break;
      scribble(nx + 38, ny + 62 + k * 42, (nw - 76) * lp * (k === 7 ? 0.6 : 1), k);
    }
    const dp = seg(t, 1.0, 2.6, E.lin), dst = '127.0.0.1'.slice(0, Math.round(dp * 9));
    const into = seg(t, 2.9, 3.8), la = 1 - seg(t, 2.9, 3.3, E.lin);
    txt('DST', 196, 196, { fam: 'mono', size: 19, color: P.dim, track: 2, a: la });
    txt(dst || '?', 266, 198, { fam: 'mono', size: 34, wt: 800, color: P.warm, a: la });
    if (into < 1) packet(lerp(290, nx + nw / 2, into), lerp(270, ny + 200, into), lerp(160, 100, into), { a: appear(t) * (1 - seg(t, 3.5, 3.9, E.lin)), glow: 0.7, dst: dst || '?' });
    const p0 = [nx + nw / 2, ny - 8], p1 = [430, -120], p2 = [YOU[0] + 18, YOU[1] - 96];
    const lp = seg(t, B1 + 0.2, B1 + 1.6);
    quadPath(p0, p1, p2, lp, P.warm, 3, [10, 9], 16);
    const rt = seg(t, B1 + 1.6, B1 + 3.4, E.io);
    if (rt > 0 && rt < 1) { const q = quad(p0, p1, p2, rt); packet(q[0], q[1], 64, { glow: 0.7, header: false }); }
    if (lp > 0) txt('back to the sender', 430, 112, { fam: 'sans', size: 22, color: P.dim, align: 'center', a: lp });
    txt('READERS', nx, ny + nh + 54, { fam: 'mono', size: 17, color: P.dim, track: 2 });
    txt('1 · you', nx + 130, ny + nh + 56, { fam: 'mono', size: 26, wt: 800, color: P.ink });
    const ex = seg(t, B1 + 2.4, B1 + 3.0, E.lin);
    if (ex > 0) txt('127.0.0.1 is the address a computer uses for itself', 196, 642, { fam: 'sans', size: 24, color: P.dim, a: ex, maxW: 790 });
  }

  function chMeditate(t, sc) {
    const B1 = sc.B[1];
    you();
    const g = lerp(1, 0.25, seg(t, 1.8, 5.4));
    packet(YOU[0], YOU[1] + 8, 52, { header: false, glow: 0.25 + 0.9 * g, a: 0.55 + 0.45 * g });
    const kx = 140, ky = 170;
    dot(kx, ky, 50, rgba(P.raise, 0.95), P.lineHi, 3);
    for (let k = 0; k <= 10; k++) {
      const a = lerp(-Math.PI * 1.25, Math.PI * 0.25, k / 10);
      ln(kx + Math.cos(a) * 58, ky + Math.sin(a) * 58, kx + Math.cos(a) * 66, ky + Math.sin(a) * 66, P.line, 2);
    }
    const ang = lerp(Math.PI * 0.25, -Math.PI * 1.0, seg(t, 1.8, 5.4));
    ln(kx, ky, kx + Math.cos(ang) * 38, ky + Math.sin(ang) * 38, P.warm, 5);
    txt('GAIN', kx, ky - 82, { fam: 'mono', size: 17, color: P.dim, align: 'center', track: 2 });
    const db = 20 * Math.log10(g), dbs = (db > -0.5 ? '0' : '−' + Math.abs(db).toFixed(0)) + ' dB';
    txt(dbs, kx, ky + 104, { fam: 'mono', size: 28, wt: 800, color: P.warm, align: 'center' });
    ln(kx + 50, ky, 250, ky, P.lineHi, 2.5);
    scope(250, 60, 720, 230, 'ALARM · WHAT YOU FEEL', (u) => Math.sin(u * 30 - t * 7) * 80 * g, P.warm);
    scope(250, 340, 720, 230, 'CONDITIONS · WHAT CAUSES IT', (u) => 52 + 14 * Math.sin(u * 11) + 9 * Math.sin(u * 29 + 1.3), P.lineHi);
    txt(dbs, 948, 98, { fam: 'mono', size: 22, wt: 800, color: P.warm, align: 'right' });
    txt('± 0 dB', 948, 378, { fam: 'mono', size: 22, wt: 800, color: P.ink, align: 'right' });
    const ex = seg(t, B1 + 0.6, B1 + 1.2, E.lin);
    if (ex > 0) txt('the alarm is quieter; the fire is the same size', 250, 634, { fam: 'sans', size: 26, color: P.dim, a: ex });
  }

  function chHobby(t, sc) {
    const B1 = sc.B[1];
    you();
    [[480, 330], [650, 300], [820, 330]].forEach(([x, y]) => person(x, y, 0.8, { color: P.lineHi, fillA: 0.05 }));
    ctx.beginPath();
    ctx.ellipse(650, 470, 290, 66, 0, 0, Math.PI * 2);
    ctx.fillStyle = rgba(P.raise, 0.92);
    ctx.fill();
    ctx.strokeStyle = P.line;
    ctx.lineWidth = 2.5;
    ctx.stroke();
    const tr = travel(t, 0.4, 2.4, [560, 445], 70, 110);
    const un = seg(t, 2.4, 4.4, E.lin);
    yarnBall(560, 458, 26 + 16 * un);
    gameBoard(762, 462);
    if (un < 1) packet(tr.x, tr.y, tr.w * (1 - 0.6 * un), { a: appear(t) * (1 - un), glow: 0.7 * (1 - un) });
    bubble(520, 176, 'nice stitch!', seg(t, 2.8, 3.2, E.lin), { tail: -30 });
    bubble(860, 208, 'your move', seg(t, 3.6, 4.0, E.lin), { tail: -20 });
    const yb = seg(t, B1 + 0.2, B1 + 0.6, E.lin), st = seg(t, B1 + 1.6, B1 + 2.2);
    bubble(204, 236, 'I’ve been so lonely…', yb, { color: P.warm, tail: -80, lean: -14, strike: st });
    if (st > 0) txt('would break the frame', 204, 300, { fam: 'mono', size: 17, wt: 700, color: P.no, align: 'center', track: 1, a: st });
    txt('PEOPLE PRESENT', 330, 604, { fam: 'mono', size: 17, color: P.dim, track: 2 });
    txt('3', 680, 606, { fam: 'mono', size: 30, wt: 800, color: P.ink });
    txt('PEOPLE INFORMED', 330, 648, { fam: 'mono', size: 17, color: P.dim, track: 2 });
    txt('0', 680, 650, { fam: 'mono', size: 30, wt: 800, color: P.no });
  }

  function chSelfCare(t, sc) {
    const B1 = sc.B[1];
    you();
    cartIcon(300, 300);
    const tr = travel(t, 0.4, 1.8, [300, 268], 70, 100);
    if (t < 2.2) packet(tr.x, tr.y, tr.w, { a: appear(t) * (1 - seg(t, 1.8, 2.2, E.lin)), glow: 0.7 });
    const tg = seg(t, 1.9, 2.4, E.back);
    if (tg > 0) priceTag(300, 196, '$24', tg);
    const rc = seg(t, 2.6, 3.6);
    if (rc > 0) receipt(lerp(320, 500, rc), 300, clamp(rc * 2));
    const dp = seg(t, 3.4, 4.0, E.lin);
    if (dp > 0) dashboard(640, 120, 330, 320, t, dp);
    const ad = seg(t, B1 + 0.6, B1 + 2.6, E.io);
    if (ad > 0) polyPath([[805, 446], [805, 536], [150, 536], [150, 490]], ad, P.gold, 3, [10, 8], 15);
    const al = seg(t, B1 + 1.4, B1 + 2.0, E.lin);
    if (al > 0) txt('recommended for you: more candles', 260, 578, { fam: 'sans', size: 24, color: P.dim, a: al });
    const ml = seg(t, B1 + 3.0, B1 + 3.6, E.lin);
    if (ml > 0) txt('suffering → sales data → more ads', 260, 638, { fam: 'mono', size: 22, wt: 700, color: P.ink, a: ml });
  }

  function chGratitude(t, sc) {
    const B1 = sc.B[1];
    you();
    const ex = 230, ey = 64, ew = 740, eh = 340;
    box(ex, ey, ew, eh, { r: 16, stroke: P.line, lw: 2, fill: rgba(P.raise, 0.92) });
    ln(ex, ey + 50, ex + ew, ey + 50, P.rule, 1.5);
    for (let k = 0; k < 3; k++) dot(ex + 28 + k * 22, ey + 25, 6, P.rule);
    txt('payload.txt', ex + ew / 2, ey + 33, { fam: 'mono', size: 16, color: P.dim, align: 'center' });
    txt('message:', ex + 34, ey + 106, { fam: 'mono', size: 17, color: P.faint, track: 1 });
    const A = 'My life lacks belonging.', Bt = 'I’m grateful for what I have.';
    const del = seg(t, B1 + 0.4, B1 + 1.8, E.lin), typ = seg(t, B1 + 2.0, B1 + 4.0, E.lin);
    const shown = del <= 0 ? A : typ <= 0 ? A.slice(0, Math.round(A.length * (1 - del))) : Bt.slice(0, Math.round(Bt.length * typ));
    const tw = txt(shown, ex + 34, ey + 180, { fam: 'sans', size: 44, wt: 700, color: typ > 0 ? P.ink : P.warm });
    const typing = (del > 0 && del < 1) || (typ > 0 && typ < 1);
    if (typing || Math.floor(t * 2.4) % 2 === 0) ln(ex + 40 + tw, ey + 140, ex + 40 + tw, ey + 192, P.ink, 3);
    const ck = seg(t, B1 + 4.2, B1 + 4.8, E.lin);
    txt('hash(original)', ex + 34, ey + 256, { fam: 'mono', size: 17, color: P.dim });
    txt('9f2c 7a41', ex + 300, ey + 256, { fam: 'mono', size: 22, wt: 800, color: P.ink });
    if (ck > 0) {
      txt('hash(sent)', ex + 34, ey + 300, { fam: 'mono', size: 17, color: P.dim, a: ck });
      txt('03be 11d8', ex + 300, ey + 300, { fam: 'mono', size: 22, wt: 800, color: P.no, a: ck });
      txt('≠', ex + 560, ey + 296, { fam: 'serif', size: 64, color: P.no, a: ck });
    }
    packet(250, 520, 170, { glow: 0.7 * (1 - typ), cells: Array.from({ length: 8 }, (_, i) => ({ color: typ * 9 > i + 1 ? P.faint : cellColor(i) })) });
    if (ck > 0) para('Rewritten at the source. The complaint never leaves.', 380, 512, 580, { fam: 'sans', size: 28, color: P.ink, a: ck });
  }

  function chMedication(t, sc) {
    const B1 = sc.B[1], B2 = sc.B[2];
    you();
    const halo = fadeIO(t, 0.5, B1 + 0.3, 0.6);
    if (halo > 0) {
      dot(YOU[0], YOU[1] - 14, 104, rgba(P.yes, 0.07 * halo), rgba(P.yes, 0.6 * halo), 2.5);
      txt('it can help someone get through', 214, 292, { fam: 'sans', size: 24, color: P.yes, a: halo });
    }
    const fx = 330, fy = 60, fw = 640, fh = 430;
    const fa = seg(t, B1 - 0.5, B1 + 0.1, E.lin);
    if (fa > 0) {
      ctx.save();
      ctx.globalAlpha *= fa;
      box(fx, fy, fw, fh, { r: 16, stroke: P.line, lw: 2, fill: rgba(P.raise, 0.92) });
      eyebrow('PHARMACY CLAIM', fx + 30, fy + 50);
      ln(fx, fy + 76, fx + fw, fy + 76, P.rule, 1.5);
      const rows = [['DX', 'F41.9 · anxiety disorder, unspecified'], ['RX', '30 tablets · 2 refills'], ['CAUSE ON RECORD', 'individual: brain chemistry'], ['SOCIAL CONTEXT', 'not recorded']];
      rows.forEach(([k, v], i) => {
        const rp = seg(t, B1 + 1.7 + i * 0.55, B1 + 2.1 + i * 0.55, E.lin), y = fy + 124 + i * 76;
        txt(k, fx + 30, y, { fam: 'mono', size: 15, color: P.faint, track: 2, a: rp });
        txt(v, fx + 30, y + 34, { fam: 'sans', size: 28, wt: 700, color: i === 3 ? P.no : P.ink, a: rp, maxW: fw - 60 });
      });
      ctx.restore();
    }
    if (t < B1) packet(152, 326, 70, { a: appear(t), glow: 0.6 });
    else {
      const tr = travel(t, B1, B1 + 1.2, [fx + 150, fy + 150], 70, 120);
      const cmp = seg(t, B1 + 1.2, B1 + 1.8);
      if (cmp < 1) packet(tr.x, tr.y, tr.w * (1 - 0.75 * cmp), { glow: 0.6, a: 1 - cmp * 0.9 });
    }
    const ag = seg(t, B2 + 0.2, B2 + 0.8, E.lin), ag2 = seg(t, B2 + 1.2, B2 + 1.8, E.lin);
    if (ag > 0) {
      txt('PRESCRIPTIONS FILLED', fx, fy + fh + 54, { fam: 'mono', size: 17, color: P.dim, track: 2, a: ag });
      txt('+1', fx + fw, fy + fh + 56, { fam: 'mono', size: 30, wt: 800, color: P.ink, align: 'right', a: ag });
      txt('NEIGHBORHOODS WITHOUT A VILLAGE', fx, fy + fh + 94, { fam: 'mono', size: 17, color: P.dim, track: 2, a: ag2 });
      txt('not counted', fx + fw, fy + fh + 96, { fam: 'mono', size: 22, wt: 800, color: P.no, align: 'right', a: ag2 });
    }
    const fn = seg(t, B2 + 3.0, B2 + 3.6, E.lin);
    if (fn > 0) para('Codes for social conditions exist (Z60.2: “problems related to living alone”). They are seldom the ones filed.', fx, 640, fw, { fam: 'sans', size: 18, color: P.faint, a: fn, lh: 1.25 });
  }

  function chApps(t, sc) {
    const B1 = sc.B[1];
    you();
    const px = 380, py = 56, pw = 230, ph = 440;
    box(px, py, pw, ph, { r: 36, stroke: P.lineHi, lw: 3, fill: rgba(P.raise, 0.92) });
    box(px + 14, py + 44, pw - 28, ph - 96, { r: 14, stroke: P.rule, lw: 1.5 });
    ln(px + pw / 2 - 26, py + 24, px + pw / 2 + 26, py + 24, P.rule, 5);
    const sx = px + pw / 2, sy = py + 44 + (ph - 96) / 2;
    if (t > 2.0) {
      swipeCard(sx, sy, 150, 210, 0, 1);
      const cyc = (t - 2.0) * 0.85, k = Math.floor(cyc), f = cyc - k;
      const dir = k % 2 ? 1 : -1, m = E.in(clamp(f * 1.5 - 0.4));
      swipeCard(sx + dir * m * 200, sy + m * 20, 150, 210, dir * 0.3 * m, 1 - m);
    }
    const tr = travel(t, 0.4, 2.0, [sx, sy], 70, 120);
    if (t < 2.4) packet(tr.x, tr.y, tr.w, { a: appear(t) * (1 - seg(t, 2.0, 2.4, E.lin)), glow: 0.7 });
    const vp = seg(t, 2.6, 3.3, E.lin);
    txt('PROFILE VECTOR', sx, py + ph + 42, { fam: 'mono', size: 15, color: P.dim, align: 'center', track: 2, a: vp });
    txt('[0.82, 0.13, 0.67, 0.91, …]', sx, py + ph + 78, { fam: 'mono', size: 20, wt: 700, color: P.warm, align: 'center', a: vp });
    const mp = seg(t, 2.6, B1 + 2.6, E.lin), months = 1 + Math.floor(13 * mp);
    eyebrow('MONTHS SUBSCRIBED', 680, 92, { size: 16 });
    txt(String(months), 680, 172, { fam: 'mono', size: 74, wt: 800, color: P.ink });
    const cx0 = 680, cy0 = 210, cw = 290, chh = 150;
    box(cx0, cy0, cw, chh, { r: 10, stroke: P.rule, lw: 1.5 });
    txt('REVENUE', cx0 + 14, cy0 + 28, { fam: 'mono', size: 14, color: P.faint, track: 2 });
    ctx.beginPath();
    for (let i = 0; i <= 14; i++) {
      const u = i / 14;
      if (u > mp + 1e-6) break;
      const x = cx0 + 14 + u * (cw - 28), y = cy0 + chh - 16 - (chh - 50) * (u * 0.85 + 0.05 * Math.sin(i * 1.7));
      if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y);
    }
    ctx.strokeStyle = P.gold;
    ctx.lineWidth = 3;
    ctx.stroke();
    const sl = seg(t, B1 + 0.6, B1 + 1.2, E.lin);
    if (sl > 0) para('A solved user is a lost subscriber.', 680, 410, 300, { fam: 'sans', size: 26, wt: 700, color: P.ink, a: sl });
    dot(840, 560, 28, P.bg, P.dead, 2.5);
    for (let k = 0; k < 5; k++) { const a = (k / 5) * Math.PI * 2; dot(840 + Math.cos(a) * 54, 560 + Math.sin(a) * 40, 7, null, P.dead, 2); }
    txt('COMMUNITY · 0 BITS', 840, 646, { fam: 'mono', size: 15, color: P.dim, align: 'center', track: 2 });
  }

  function chSelfHelp(t, sc) {
    const B1 = sc.B[1];
    you();
    const sx = 620, sy = 92;
    box(sx - 230, sy - 46, 460, 92, { r: 16, stroke: P.lineHi, lw: 2.5, fill: rgba(P.raise, 0.92) });
    txt('BOOKS · PODCASTS · FEEDS', sx, sy + 8, { fam: 'mono', size: 18, wt: 700, color: P.ink, align: 'center', track: 2 });
    const grow = seg(t, B1 + 0.2, B1 + 3.0, E.lin), visible = Math.round(18 + 18 * grow);
    for (let k = 0; k < visible; k++) {
      const c = k % 9, r = (k / 9) | 0, x = 300 + c * 80, y = 300 + r * 80;
      if (t > 0.8) {
        const ph = (t * 0.55 + k * 0.137) % 1;
        dot(lerp(sx, x, ph), lerp(sy + 46, y - 30, ph), 4, rgba(P.gold, 0.85 * (1 - ph)));
      }
      person(x, y, 0.38, { color: P.line, fillA: 0.08, lw: 0.8 });
    }
    const up = seg(t, 2.0, 3.2);
    if (up > 0) {
      const ex = lerp(132, 300, up), ey = lerp(318, 176, up);
      ln(132, 318, ex, ey, P.warm, 3, [8, 8]);
      if (up >= 1) {
        cross(312, 166, 13, P.no, 4);
        txt('UPLINK · 0 BITS', 140, 150, { fam: 'mono', size: 17, wt: 700, color: P.no, track: 2 });
      }
    }
    txt('DOWNLINK', 300, 612, { fam: 'mono', size: 16, color: P.dim, track: 2 });
    txt('their words reach everyone', 450, 614, { fam: 'sans', size: 24, color: P.ink });
    txt('UPLINK', 300, 654, { fam: 'mono', size: 16, color: P.dim, track: 2 });
    txt('yours reach no one', 450, 656, { fam: 'sans', size: 24, color: P.no });
  }

  function chHR(t, sc) {
    const B1 = sc.B[1];
    you();
    const bx = 470, by = 50, bw = 500, bh = 520;
    ctx.beginPath();
    ctx.moveTo(bx - 14, by + 84);
    ctx.lineTo(bx + bw / 2, by);
    ctx.lineTo(bx + bw + 14, by + 84);
    ctx.closePath();
    ctx.fillStyle = rgba(P.power, 0.06);
    ctx.fill();
    ctx.strokeStyle = P.power;
    ctx.lineWidth = 2.5;
    ctx.lineJoin = 'round';
    ctx.stroke();
    box(bx, by + 84, bw, bh - 84, { r: 4, stroke: P.power, lw: 2.5, fill: rgba(P.power, 0.04) });
    txt('THE INSTITUTION', bx + bw / 2, by + 66, { fam: 'mono', size: 15, wt: 700, color: P.power, align: 'center', track: 3 });
    const dx = bx + 30, dy = by + bh - 136;
    box(dx, dy, 96, 136, { r: 4, stroke: P.power, lw: 2.5 });
    txt('HR', dx + 48, dy + 56, { fam: 'mono', size: 28, wt: 800, color: P.power, align: 'center' });
    const tr = travel(t, 0.4, 2.0, [dx + 48, dy + 90], 70, 80);
    const inn = seg(t, 2.0, 2.8);
    const px = lerp(tr.x, bx + 250, inn), py = lerp(tr.y, by + 170, inn), pw = lerp(tr.w, 150, inn);
    const relabeled = t > 3.0;
    packet(px, py, pw, { a: appear(t), glow: 0.5 * (1 - seg(t, 2.8, 3.4, E.lin)), stroke: relabeled ? P.power : undefined, cellColor: relabeled ? P.power : undefined });
    stamp('LIABILITY', bx + 262, by + 178, seg(t, 3.0, 3.6, E.lin), P.no, 28, -0.08);
    [['abuse of power', 'legal exposure'], ['overwork', 'performance issue'], ['isolation', 'culture fit']].forEach(([a, b], i) => {
      const ip = seg(t, B1 + 0.2 + i * 0.9, B1 + 0.8 + i * 0.9, E.lin);
      if (ip <= 0) return;
      const x = bx + 160, y = by + 276 + i * 84;
      const w = txt(a, x, y, { fam: 'sans', size: 25, color: P.warm, a: ip });
      ln(x - 2, y - 8, x - 2 + (w + 4) * seg(t, B1 + 0.6 + i * 0.9, B1 + 1.0 + i * 0.9, E.lin), y - 8, P.no, 2.5);
      txt('↳ ' + b, x + 10, y + 34, { fam: 'sans', size: 25, wt: 700, color: P.power, a: ip });
    });
    const op = seg(t, B1 + 3.4, B1 + 4.0, E.lin);
    if (op > 0) {
      txt('OUTPUT', bx, by + bh + 42, { fam: 'mono', size: 16, color: P.dim, track: 2, a: op });
      txt('a file on you, and a plan for managing you', bx, by + bh + 80, { fam: 'sans', size: 24, wt: 700, color: P.ink, a: op, maxW: 500 });
    }
  }

  function chVote(t, sc) {
    const B1 = sc.B[1];
    you();
    const fx = 380, fw = 300, cx = fx + fw / 2;
    ln(fx, 36, fx, 380, P.lineHi, 4);
    ln(fx + fw, 36, fx + fw, 380, P.lineHi, 4);
    ln(fx - 24, 36, fx + fw + 24, 36, P.lineHi, 6);
    const down = seg(t, 2.0, 2.6, E.in), up = seg(t, 3.2, 4.0, E.io);
    const plateY = lerp(100, 300, down) - lerp(0, 160, up);
    ln(cx, 36, cx, plateY - 26, P.line, 8);
    box(fx + 12, plateY - 26, fw - 24, 26, { r: 4, fill: P.line });
    box(fx + 12, 330, fw - 24, 22, { r: 4, fill: P.line });
    txt('COMPRESSION', cx, 410, { fam: 'mono', size: 16, color: P.dim, align: 'center', track: 3 });
    const tr = travel(t, 0.4, 1.8, [cx, 292], 70, 170);
    const crush = seg(t, 2.45, 2.6, E.lin), sy = 1 - crush * 0.88;
    const pyc = tr.p >= 1 ? 329 - 37.4 * sy : tr.y;
    if (t < 2.9) packet(tr.x, pyc, tr.w, { a: appear(t) * (1 - seg(t, 2.6, 2.9, E.lin)), glow: 0.7, sy });
    const chip = seg(t, 2.8, 3.3, E.back), mv = seg(t, 3.9, 4.9);
    if (chip > 0 && mv < 1) checkbox(lerp(cx, 806, mv), lerp(312, 206, mv), 44 * clamp(chip), true, P.ink);
    txt('8 fields → 1 bit', cx, 470, { fam: 'mono', size: 26, wt: 800, color: P.ink, align: 'center', a: seg(t, 3.0, 3.6, E.lin) });
    box(760, 60, 212, 220, { r: 14, stroke: P.power, lw: 2.5, fill: rgba(P.raise, 0.92) });
    txt('BALLOT', 866, 100, { fam: 'mono', size: 16, wt: 700, color: P.power, align: 'center', track: 3 });
    const filled = mv >= 1;
    [['A', 158], ['B', 214]].forEach(([s, y], i) => {
      dot(806, y - 8, 14, i === 1 && filled ? P.ink : P.raise, P.ink, 2.5);
      txt('option ' + s, 834, y, { fam: 'sans', size: 24, color: P.ink });
    });
    txt('options picked by', 866, 316, { fam: 'sans', size: 20, color: P.dim, align: 'center' });
    txt('someone else', 866, 342, { fam: 'sans', size: 20, color: P.dim, align: 'center' });
    const tl = seg(t, B1 + 0.2, B1 + 1.0, E.lin);
    if (tl > 0) {
      ctx.save();
      ctx.globalAlpha *= tl;
      const ax0 = 160, ax1 = 960, ay = 540;
      ln(ax0, ay, ax1, ay, P.lineHi, 2.5);
      for (let k = 0; k <= 4; k++) {
        const x = lerp(ax0, ax1, k / 4);
        ln(x, ay - 8, x, ay + 8, P.lineHi, 2);
        txt(k === 0 ? 'year 0' : String(k), x, ay + 36, { fam: 'mono', size: 16, color: P.dim, align: 'center' });
      }
      const pulse = seg(t, B1 + 1.0, B1 + 4.0, E.lin);
      dot(ax0, ay, 10, P.warm);
      if (pulse < 1) dot(lerp(ax0, ax1, pulse), ay, 7, rgba(P.warm, 0.5)); else dot(ax1, ay, 10, P.warm);
      txt('one send', ax0, ay - 22, { fam: 'sans', size: 20, color: P.dim, align: 'center' });
      txt('the next one', ax1, ay - 22, { fam: 'sans', size: 20, color: P.dim, align: 'right' });
      ctx.restore();
    }
    const mt = seg(t, B1 + 2.2, B1 + 2.8, E.lin);
    if (mt > 0) {
      const mono = { it: false, fam: 'mono', wt: 700 };
      rich([['1 bit ÷ 126,230,400 s ≈ 7.9 × 10', mono], ['−9', Object.assign({ sup: true }, mono)], [' bit/s', mono]], 160, 622, { size: 24, color: P.ink, a: mt });
      txt('a conversation carries about 39 bit/s, some 5 billion times more', 160, 660, { fam: 'sans', size: 22, color: P.dim, a: seg(t, B1 + 3.2, B1 + 3.8, E.lin), maxW: 800 });
    }
  }

  function chPrivate(t, sc) {
    const B1 = sc.B[1];
    you();
    const wx = 450, ww = 64, wy = 40, wh = 600;
    box(wx, wy, ww, wh, { r: 4, fill: rgba(P.line, 0.22), stroke: P.lineHi, lw: 2.5 });
    for (let r = 1; r < 15; r++) ln(wx + 2, wy + r * 40, wx + ww - 2, wy + r * 40, rgba(P.lineHi, 0.5), 1.5);
    for (let r = 0; r < 15; r++) { const x = wx + (r % 2 ? ww * 0.33 : ww * 0.66); ln(x, wy + r * 40, x, wy + r * 40 + 40, rgba(P.lineHi, 0.5), 1.5); }
    placard('keep it private', wx + ww / 2, 120, -0.05, seg(t, 0.3, 0.7, E.lin));
    placard('don’t air your dirty laundry', wx + ww / 2, 210, 0.04, seg(t, 0.6, 1.0, E.lin));
    placard('don’t make it weird', wx + ww / 2, 300, -0.03, seg(t, 0.9, 1.3, E.lin));
    const hitX = wx - 58;
    const att = (t0) => {
      const go = seg(t, t0, t0 + 0.8, E.in), back = seg(t, t0 + 0.8, t0 + 1.5, E.out);
      return lerp(170, hitX, go) - (hitX - 230) * back;
    };
    const x = t < 2.9 ? att(1.2) : att(3.2);
    const hit = Math.max(fadeIO(t, 1.95, 2.25, 0.15), fadeIO(t, 3.95, 4.25, 0.15));
    packet(x, 440, 110, { glow: 0.7, a: appear(t), sx: 1 - hit * 0.2, sy: 1 + hit * 0.25 });
    stamp('DROP', 800, 130, seg(t, 2.0, 2.5, E.lin), P.no, 54, -0.06);
    const xp = seg(t, 2.6, 3.2, E.lin);
    if (xp > 0) {
      txt('!X', 700, 292, { fam: 'mono', size: 48, wt: 800, color: P.no, a: xp });
      para('traceroute’s code for “communication administratively prohibited”', 700, 334, 280, { fam: 'sans', size: 21, color: P.dim, a: xp });
    }
    for (let k = 0; k < 4; k++) person(620 + k * 96, 540, 0.62, { color: P.dead, fillA: 0.04, a: 0.8 });
    txt('THE OTHER SIDE · 0 INFORMED', 610, 640, { fam: 'mono', size: 16, color: P.dim, track: 2, a: seg(t, B1 + 0.4, B1 + 1.0, E.lin) });
  }

  /* ================= outward chambers ================= */
  const TRUTH = (() => {
    const r = rng(21), cx = 500, cy = 360, peers = [];
    for (let k = 0; k < 12; k++) {
      const a = (k / 12) * Math.PI * 2 + 0.26, x = cx + Math.cos(a) * 400, y = cy + Math.sin(a) * 250;
      peers.push({ x, y, d: Math.hypot(x - cx, y - cy + 40), share: Array.from({ length: 8 }, (_, i) => (i >= 3 ? r() < 0.7 : r() < 0.85)) });
    }
    const edges = [];
    for (let k = 0; k < 12; k++) { edges.push([k, (k + 1) % 12]); if (k % 3 === 0) edges.push([k, (k + 5) % 12]); }
    return { cx, cy, peers, edges };
  })();
  function chTruth(t, sc) {
    const B1 = sc.B[1], { cx, cy, peers, edges } = TRUTH, v = 300, t0 = B1 - 0.4;
    for (let k = 0; k < 4; k++) {
      const st = t0 + k * 1.3;
      if (t < st) continue;
      const R = (t - st) * v;
      if (R < 620) ring(cx, cy - 40, R, 0.7 * (1 - R / 620), P.warm, 3);
    }
    const hitT = (p) => t0 + p.d / v;
    edges.forEach(([i, j]) => {
      const h = Math.max(hitT(peers[i]), hitT(peers[j])), a = seg(t, h + 0.9, h + 1.6, E.lin);
      if (a > 0) ln(peers[i].x, peers[i].y - 20, peers[j].x, peers[j].y - 20, rgba(P.warm, 0.45 * a), 2);
    });
    peers.forEach((p) => {
      const lit = seg(t, hitT(p), hitT(p) + 0.5, E.lin);
      person(p.x, p.y, 0.6, { color: lit > 0.5 ? P.warm : P.dead, fillA: 0.05 + 0.12 * lit });
      if (lit > 0) packet(p.x, p.y - 76, 58, { a: lit, header: false, cells: p.share.map((s, i) => ({ color: s ? cellColor(i) : P.rule })) });
    });
    person(cx, cy, 1, { label: 'YOU' });
    packet(cx, cy - 116, 120, { glow: 0.9 + 0.2 * Math.sin(t * 3), dst: 'anyone' });
    const informed = peers.filter((p) => t >= hitT(p)).length;
    eyebrow('HUMANS INFORMED', 20, 40, { size: 15 });
    txt(String(informed), 20, 100, { fam: 'mono', size: 54, wt: 800, color: informed ? P.warm : P.dim });
  }

  const SNR = (() => {
    const M = 150, NMAX = 256, r = rng(7);
    const bump = (u, c, w) => Math.exp(-((u - c) * (u - c)) / (2 * w * w));
    const s = new Float32Array(M);
    for (let i = 0; i < M; i++) {
      const u = i / (M - 1);
      s[i] = 0.18 + 0.62 * bump(u, 0.2, 0.05) + 0.85 * bump(u, 0.5, 0.065) + 0.55 * bump(u, 0.8, 0.045);
    }
    const cum = new Float32Array((NMAX + 1) * M), traces = [];
    for (let n = 0; n < NMAX; n++) {
      const comps = [];
      for (let k = 0; k < 6; k++) comps.push({ f: 0.6 + r() * 7, ph: r() * Math.PI * 2, a: (r() - 0.5) * 1.0 });
      const tr = new Float32Array(M);
      for (let i = 0; i < M; i++) {
        const u = i / (M - 1);
        let v = 0;
        for (const c of comps) v += c.a * Math.sin(c.f * u * Math.PI * 2 + c.ph);
        tr[i] = s[i] + v + (r() - 0.5) * 0.35;
      }
      if (n < 24) traces.push(tr);
      for (let i = 0; i < M; i++) cum[(n + 1) * M + i] = cum[n * M + i] + tr[i];
    }
    return { M, s, cum, traces };
  })();
  const PLOT = { x: 80, y: 50, w: 880, h: 420, lo: -0.9, hi: 1.9 };
  const plotY = (v) => PLOT.y + PLOT.h - ((v - PLOT.lo) / (PLOT.hi - PLOT.lo)) * PLOT.h;
  const plotX = (i) => PLOT.x + 16 + (i / (SNR.M - 1)) * (PLOT.w - 32);
  function plotLine(getV, color, lw, a, dash) {
    if (a <= 0) return;
    ctx.save();
    ctx.globalAlpha *= a;
    ctx.beginPath();
    for (let i = 0; i < SNR.M; i++) { const x = plotX(i), y = plotY(getV(i)); if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); }
    ctx.strokeStyle = color;
    ctx.lineWidth = lw;
    ctx.lineJoin = 'round';
    if (dash) ctx.setLineDash(dash);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
  }
  function plotFrame() {
    box(PLOT.x, PLOT.y, PLOT.w, PLOT.h, { r: 12, stroke: P.line, lw: 2, fill: rgba(P.raise, 0.55) });
    for (let k = 1; k < 4; k++) ln(PLOT.x + 2, PLOT.y + (PLOT.h * k) / 4, PLOT.x + PLOT.w - 2, PLOT.y + (PLOT.h * k) / 4, P.grid, 1.5);
    txt('STRAIN', PLOT.x + 18, PLOT.y + 32, { fam: 'mono', size: 14, color: P.faint, track: 2 });
    txt('ONE MONTH OF SOMEONE’S LIFE →', PLOT.x + PLOT.w - 18, PLOT.y + PLOT.h - 18, { fam: 'mono', size: 14, color: P.faint, align: 'right', track: 2 });
  }
  function snrN(t, sc) {
    const B1 = sc.B[1], B2 = sc.B[2];
    if (t < B1) return 1;
    if (t < B2) return 2 << clamp(Math.floor(((t - B1) / (B2 - B1)) * 6), 0, 5);
    return t < B2 + 3.2 ? 16 : 256;
  }
  const rootStr = (n) => { const r = Math.sqrt(n); return Number.isInteger(r) ? String(r) : r.toFixed(1); };
  function chNotes(t, sc) {
    const N = snrN(t, sc), D = sc.dur;
    plotFrame();
    ctx.save();
    rr(PLOT.x, PLOT.y, PLOT.w, PLOT.h, 12);
    ctx.clip();
    for (let n = 0; n < Math.min(N, 24); n++) plotLine((i) => SNR.traces[n][i], P.dim, 1.4, N === 1 ? 0.9 : 0.16);
    plotLine((i) => SNR.cum[N * SNR.M + i] / N, P.warm, N === 1 ? 3 : 4, 1);
    const tru = seg(t, D - 3.2, D - 2.4, E.lin);
    if (tru > 0) plotLine((i) => SNR.s[i], P.gold, 2.5, tru, [10, 8]);
    ctx.restore();
    txt('N', PLOT.x, 548, { fam: 'serif', it: true, size: 42, color: P.dim });
    txt(N.toLocaleString('en-US'), PLOT.x + 42, 550, { fam: 'mono', size: 54, wt: 800, color: P.ink });
    txt('particulars ÷ ' + rootStr(N), 430, 528, { fam: 'mono', size: 21, color: P.dim });
    txt('clarity × ' + rootStr(N), 430, 568, { fam: 'mono', size: 28, wt: 800, color: P.warm });
    const msg = N === 1 ? 'one story alone reads as a personal problem' : N < 16 ? 'a shape starts to show through' : N < 256 ? 'the shared part is unmistakable' : 'the shared conditions, plain as day';
    txt(msg, PLOT.x, 640, { fam: 'sans', size: 26, color: P.ink });
    if (tru > 0) txt('dashed: the shared conditions', 960, 640, { fam: 'sans', size: 20, color: P.gold, align: 'right', a: tru });
  }

  function chName(t) {
    plotFrame();
    ctx.save();
    rr(PLOT.x, PLOT.y, PLOT.w, PLOT.h, 12);
    ctx.clip();
    plotLine((i) => SNR.cum[256 * SNR.M + i] / 256, P.warm, 4, 1);
    ctx.restore();
    [[0.2, 'rent due'], [0.5, 'the overtime'], [0.8, 'nobody to call']].forEach(([u, label], i) => {
      const p = seg(t, 0.9 + i * 0.5, 1.4 + i * 0.5, E.back);
      if (p <= 0) return;
      const i0 = Math.round(u * (SNR.M - 1)), x = plotX(i0), y = plotY(SNR.s[i0]) - 22;
      ctx.save();
      ctx.globalAlpha *= clamp(p);
      ln(x, y, x, y - 34 * p, P.ink, 2);
      const w = measure(label, { fam: 'sans', size: 22, wt: 700 }) + 24;
      box(x - w / 2, y - 34 * p - 38, w, 38, { r: 8, fill: P.raise, stroke: P.ink, lw: 2 });
      txt(label, x, y - 34 * p - 12, { fam: 'sans', size: 22, wt: 700, color: P.ink, align: 'center' });
      ctx.restore();
    });
    const nm = seg(t, 2.6, 3.2, E.lin);
    if (nm > 0) {
      txt('NAMED', PLOT.x, 548, { fam: 'mono', size: 19, wt: 800, color: P.warm, track: 3, a: nm });
      txt('the same conditions, not a personal failing', PLOT.x, 592, { fam: 'sans', size: 30, wt: 700, color: P.ink, a: nm, maxW: 860 });
    }
    ['it’s just you', 'have you tried yoga?', 'be grateful'].forEach((d, i) => {
      const t0 = 3.4 + i * 1.15, go = seg(t, t0, t0 + 0.55, E.in), back = seg(t, t0 + 0.55, t0 + 1.3, E.out);
      if (go <= 0 || back >= 1) return;
      const y = 252 + i * 70, x = lerp(860, 700, go) + back * 150, w = measure(d, { fam: 'sans', size: 22 }) + 26;
      ctx.save();
      ctx.globalAlpha *= 1 - back;
      ctx.translate(x, y + back * 30);
      ctx.rotate(back * 0.25);
      box(-w / 2, -20, w, 40, { r: 20, fill: P.raise, stroke: P.dead, lw: 2 });
      txt(d, 0, 8, { fam: 'sans', size: 22, color: P.dim, align: 'center' });
      ctx.restore();
      if (go >= 1) ring(700 - w / 2, y, 14 + back * 50, 0.8 * (1 - back), P.warm, 3);
    });
    const ds = seg(t, 6.6, 7.2, E.lin);
    if (ds > 0) txt('dismissals bounce off a named pattern', 960, 640, { fam: 'sans', size: 20, color: P.dim, align: 'right', a: ds });
  }

  const ORG = (() => { const r = rng(11); return Array.from({ length: 150 }, () => ({ x: 40 + r() * 920, y: 520 + r() * 110, d: r() * 1.5 })); })();
  function chOrganize(t) {
    const cx0 = 190, cy0 = 26, cw = 620, chh = 132, arrive = seg(t, 6.2, 6.8, E.lin);
    box(cx0, cy0, cw, chh, { r: 14, stroke: P.power, lw: 2.5, fill: rgba(P.power, 0.05 + 0.06 * arrive) });
    txt('WHOEVER CONTROLS THE CONDITIONS', cx0 + cw / 2, cy0 + 38, { fam: 'mono', size: 15, wt: 700, color: P.power, align: 'center', track: 2 });
    ['housing', 'food', 'wages', 'power'].forEach((lab, i) => {
      const x = cx0 + 90 + i * 148;
      dot(x - 50, cy0 + 90, 8, arrive > 0 ? rgba(P.yes, arrive) : null, arrive > 0 ? P.yes : P.rule, 2.5);
      txt(lab, x + 6, cy0 + 98, { fam: 'sans', size: 26, wt: 700, color: P.ink, align: 'center' });
    });
    const mx = 500, my = 380;
    ORG.forEach((d) => dot(d.x, d.y + 16, 5, rgba(P.warm, 0.5)));
    txt('1,000 PEOPLE, EACH WITH THE SAME 8 FIELDS', 500, 676, { fam: 'mono', size: 15, color: P.dim, align: 'center', track: 2 });
    ORG.forEach((d) => {
      const p = seg(t, 0.8 + d.d, 2.6 + d.d, E.io);
      if (p > 0 && p < 1) packet(lerp(d.x, mx, p), lerp(d.y, my, p), 30, { header: false, a: 0.95 - p * 0.3 });
    });
    const grow = seg(t, 2.6, 4.4, E.out), rise = seg(t, 4.8, 6.4, E.io);
    const py = lerp(my, cy0 + chh / 2, rise);
    if (rise > 0) {
      ln(mx, my, mx, Math.max(py, cy0 + chh + 12), rgba(P.warm, 0.85), 6);
      if (arrive > 0) arrowHead(mx, cy0 + chh + 4, -Math.PI / 2, 22, P.warm);
    }
    if (grow > 0 && arrive < 1) {
      const w = lerp(40, 300, grow) * lerp(1, 0.6, rise);
      packet(mx, py, w, { glow: 1.1, dst: 'whoever controls the conditions', a: 1 - arrive });
    }
    if (grow > 0) {
      const ly = rise > 0 ? my + 10 : my + 92;
      txt('ONE DEMAND · 1,000 VOICES · 8 OF 8 FIELDS', mx, ly + 6, { fam: 'mono', size: 17, wt: 700, color: P.ink, align: 'center', track: 2, a: grow });
    }
    if (arrive > 0) txt('RECEIVED INTACT', mx + 28, cy0 + chh + 66, { fam: 'mono', size: 22, wt: 800, color: P.yes, track: 3, a: arrive });
  }

  const AID = {
    nodes: [[110, 150], [300, 90], [480, 170], [190, 320], [390, 320], [100, 500], [290, 560], [500, 470]],
    edges: [[0, 1], [1, 2], [0, 3], [3, 4], [2, 4], [3, 5], [5, 6], [6, 7], [4, 7], [1, 4], [4, 6]],
    deliveries: [[0, 1, 'food'], [4, 7, 'ride'], [3, 5, 'care'], [2, 4, 'room'], [6, 7, 'food'], [1, 4, 'rent'], [5, 6, 'ride'], [0, 3, 'call']],
  };
  function chAid(t) {
    const { nodes, edges, deliveries } = AID;
    edges.forEach(([a, b]) => ln(nodes[a][0], nodes[a][1], nodes[b][0], nodes[b][1], rgba(P.warm, 0.4), 2.5));
    deliveries.forEach(([a, b, lab], i) => {
      const t0 = 0.9 + i * 0.85, p = seg(t, t0, t0 + 1.0, E.io);
      if (p <= 0 || p >= 1) return;
      const x = lerp(nodes[a][0], nodes[b][0], p), y = lerp(nodes[a][1], nodes[b][1], p), w = measure(lab, { fam: 'sans', size: 18, wt: 700 }) + 20;
      box(x - w / 2, y - 15, w, 30, { r: 15, fill: P.gold });
      txt(lab, x, y + 6, { fam: 'sans', size: 18, wt: 700, color: P.bg, align: 'center' });
    });
    nodes.forEach(([x, y]) => person(x, y + 20, 0.55, { color: P.warm, fillA: 0.14 }));
    box(630, 40, 350, 600, { r: 16, fill: rgba(P.raise, 0.92), stroke: P.rule, lw: 2 });
    eyebrow('WHAT’S MISSING', 654, 86, { size: 16 });
    txt('example', 956, 86, { fam: 'sans', size: 17, color: P.faint, align: 'right' });
    [['groceries', '9 households'], ['rides', '14 a week'], ['childcare', '6 hours a week'], ['spare rooms', '3 short'], ['rent gap', '2 families'], ['someone to call', 'everyone']].forEach(([k, v], i) => {
      const p = seg(t, 1.7 + i * 0.85, 2.1 + i * 0.85, E.lin), y = 146 + i * 72;
      txt(k, 654, y, { fam: 'sans', size: 26, wt: 700, color: P.ink, a: p });
      txt(v, 654, y + 30, { fam: 'mono', size: 18, color: P.warm, a: p });
    });
    txt('learned by doing it', 654, 610, { fam: 'sans', size: 22, color: P.dim, a: seg(t, 7.0, 7.6, E.lin) });
  }

  /* ================= side panels ================= */
  function reportSide(d, t, sc) {
    const D = sc.dur, r0 = 1.0, r1 = Math.max(3.4, D * 0.52), step = (r1 - r0) / 5;
    const gp = seg(t, D * 0.58, D * 0.7, E.lin), sp = seg(t, D * 0.74, D * 0.74 + 0.7, E.lin), col = binColor(d.bin);
    const rowP = (i) => seg(t, r0 + i * step, r0 + i * step + 0.5, E.out);
    const head = d.host ? String(d.n).padStart(2, ' ') + '  ' + d.host + '   ' + d.reply : 'outward route ' + d.n + ' of 5';
    SIDE(() => {
      card(674, 680);
      eyebrow('DELIVERY REPORT', 32, 54);
      txt(d.code, 642, 54, { fam: 'mono', size: 18, color: P.faint, align: 'right', track: 2 });
      txt(head, 32, 96, { fam: 'mono', size: 20, color: P.ink, maxW: 610, min: 13 });
      ln(32, 116, 642, 116, P.rule, 1.5);
      d.report.forEach(([k, v], i) => {
        const p = rowP(i), y = 154 + i * 62;
        txt(k, 32, y, { fam: 'mono', size: 15, wt: 500, color: P.faint, track: 2, a: p });
        txt(v, 32, y + 32, { fam: 'sans', size: 28, wt: 700, color: P.ink, a: p, maxW: 610, min: 18 });
      });
      ln(32, 456, 642, 456, P.rule, 1.5);
      gatesRow(32, 476, d.gates, gp, {});
      stamp(d.status, 337, 630, sp, col, 32, -0.05);
    }, () => {
      card(780, 340);
      eyebrow('DELIVERY REPORT · ' + d.code, 26, 42, { size: 17 });
      d.report.forEach(([k, v], i) => {
        const p = rowP(i), y = 86 + i * 52;
        txt(k, 26, y - 1, { fam: 'sans', size: 18, wt: 700, color: P.faint, track: 1, a: p });
        txt(v, 26, y + 26, { fam: 'sans', size: 25, wt: 700, color: P.ink, a: p, maxW: 410, min: 16 });
      });
      const gy = gatesGrid(458, 60, d.gates, gp, { tw: 146, th: 64, g: 12 });
      stamp(d.status, 458 + 152, gy + 30, sp, col, 24, -0.05);
    });
  }

  function binsPanel(counts, t, title, opt) {
    opt = opt || {};
    const max = opt.max || 5;
    SIDE(() => {
      card(674, 680);
      eyebrow(title, 32, 56, { maxW: 610 });
      BIN_ORDER.forEach((k, i) => {
        const y = 120 + i * 78, col = binColor(k), v = counts[k] || 0, n = Math.round(v);
        if (opt.pulse && opt.pulse.indexOf(k) >= 0 && opt.pulseA > 0) box(16, y - 40, 642, 72, { r: 12, stroke: rgba(col, opt.pulseA * (0.55 + 0.45 * Math.sin(t * 5))), lw: 2.5 });
        binIcon(k, 56, y - 6, 1.15, col);
        txt(BINS[k].name, 96, y, { fam: 'mono', size: 20, wt: 700, color: P.ink, track: 2 });
        txt(BINS[k].desc, 96, y + 28, { fam: 'sans', size: 19, color: P.dim, maxW: 300, min: 14 });
        const bw = 150 * clamp(v / max);
        if (bw > 0.5) box(424, y - 14, bw, 16, { r: 4, fill: col }); else ln(424, y - 6, 574, y - 6, P.rule, 1.5, [3, 6]);
        txt(String(n), 642, y + 6, { fam: 'mono', size: 30, wt: 800, color: n ? P.ink : P.no, align: 'right' });
      });
    }, () => {
      card(780, 340);
      eyebrow(title, 26, 44, { size: 17, maxW: 728 });
      BIN_ORDER.forEach((k, i) => {
        const col2 = i < 4 ? 0 : 1, row = i < 4 ? i : i - 4, x = 26 + col2 * 384, y = 104 + row * 62, n = Math.round(counts[k] || 0);
        if (opt.pulse && opt.pulse.indexOf(k) >= 0 && opt.pulseA > 0) box(x - 8, y - 36, 360, 54, { r: 10, stroke: rgba(binColor(k), opt.pulseA * (0.55 + 0.45 * Math.sin(t * 5))), lw: 2.5 });
        binIcon(k, x + 18, y - 8, 1, binColor(k));
        txt(BINS[k].name, x + 50, y, { fam: 'mono', size: 19, wt: 700, color: P.ink, track: 1.5 });
        txt(String(n), x + 340, y + 2, { fam: 'mono', size: 28, wt: 800, color: n ? P.ink : P.no, align: 'right' });
      });
    });
  }

  function legendPanel(t) {
    SIDE(() => {
      card(674, 680);
      eyebrow('WHERE A PACKET CAN END UP', 32, 56);
      BIN_ORDER.forEach((k, i) => {
        const y = 124 + i * 78, p = seg(t, 1.0 + i * 0.25, 1.5 + i * 0.25, E.lin);
        ctx.save();
        ctx.globalAlpha *= 0.3 + 0.7 * p;
        binIcon(k, 56, y - 6, 1.15, binColor(k));
        txt(BINS[k].name, 96, y, { fam: 'mono', size: 20, wt: 700, color: P.ink, track: 2 });
        txt(BINS[k].desc, 96, y + 30, { fam: 'sans', size: 21, color: P.dim, maxW: 540 });
        ctx.restore();
      });
    }, () => {
      card(780, 340);
      eyebrow('WHERE A PACKET CAN END UP', 26, 44, { size: 17 });
      BIN_ORDER.forEach((k, i) => {
        const col2 = i < 4 ? 0 : 1, row = i < 4 ? i : i - 4, x = 26 + col2 * 384, y = 100 + row * 62;
        binIcon(k, x + 18, y - 8, 1, binColor(k));
        txt(BINS[k].name, x + 50, y, { fam: 'mono', size: 18, wt: 700, color: P.ink, track: 1.5 });
        txt(BINS[k].desc, x + 50, y + 26, { fam: 'sans', size: 18, color: P.dim, maxW: 310, min: 13 });
      });
    });
  }

  const VEC = [['p = (', {}], ['n', {}], ['1', { sub: 1 }], [' n', {}], ['2', { sub: 1 }], [' n', {}], ['3', { sub: 1 }], [' | c', {}], ['1', { sub: 1 }], [' c', {}], ['2', { sub: 1 }], [' c', {}], ['3', { sub: 1 }], [' c', {}], ['4', { sub: 1 }], [' c', {}], ['5', { sub: 1 }], [')', {}]];
  function vectorPanel(t, sc) {
    const B1 = sc.B[1], la = seg(t, B1, B1 + 0.6, E.lin);
    SIDE(() => {
      card(674, 680);
      eyebrow('THE PACKET AS A VECTOR', 32, 56);
      rich(VEC, 32, 140, { size: 40 });
      dot(44, 198, 9, P.gold);
      txt('n  needs: what the person is missing', 66, 206, { fam: 'sans', size: 25, color: P.ink, maxW: 580 });
      dot(44, 248, 9, P.warm);
      txt('c  conditions: what produced the need', 66, 256, { fam: 'sans', size: 25, color: P.ink, maxW: 580 });
      ln(32, 300, 642, 300, P.rule, 1.5);
      rich([['|p| = 8', {}], [' fields', { it: false, fam: 'sans' }]], 32, 366, { size: 44 });
      para('At every hop, the delivery report counts how many of the eight fields travel beyond the first receiver.', 32, 430, 610, { fam: 'sans', size: 24, color: P.dim, lh: 1.3 });
      para('The header is addressed to whoever controls the conditions. Watch who actually receives it.', 32, 548, 610, { fam: 'sans', size: 24, color: P.dim, lh: 1.3, a: la });
    }, () => {
      card(780, 340);
      eyebrow('THE PACKET AS A VECTOR', 26, 46, { size: 17 });
      rich(VEC, 26, 116, { size: 38 });
      dot(36, 168, 8, P.gold);
      txt('n  needs: what the person is missing', 56, 176, { fam: 'sans', size: 24, color: P.ink, maxW: 700 });
      dot(36, 212, 8, P.warm);
      txt('c  conditions: what produced the need', 56, 220, { fam: 'sans', size: 24, color: P.ink, maxW: 700 });
      para('Each hop’s report counts how many of the 8 fields travel beyond the first receiver.', 26, 280, 730, { fam: 'sans', size: 23, color: P.dim, lh: 1.25 });
    });
  }

  function equationPanel(t, sc) {
    const B2 = sc.B[2], B3 = sc.B[3];
    const zp = seg(t, B2 + 0.4, B2 + 1.0, E.lin), np = seg(t, B3 + 0.3, B3 + 0.9, E.lin);
    SIDE(() => {
      card(674, 680);
      eyebrow('THE PRODUCT', 32, 56);
      txt('change is possible only if', 32, 124, { fam: 'sans', size: 28, color: P.dim });
      txt('OUT × INTACT', 32, 186, { fam: 'mono', size: 36, wt: 800, color: P.ink });
      txt('× SIDEWAYS × UPWARD', 32, 238, { fam: 'mono', size: 36, wt: 800, color: P.ink, maxW: 610 });
      txt('= 1', 32, 300, { fam: 'mono', size: 44, wt: 800, color: P.yes });
      ln(32, 340, 642, 340, P.rule, 1.5);
      txt('each test scores 0 or 1', 32, 392, { fam: 'sans', size: 26, color: P.ink, a: zp });
      rich([['0 × anything = 0', {}]], 32, 462, { size: 46, color: P.no, a: zp });
      para('Necessary, not sufficient. Passing all four makes change possible, not certain.', 32, 540, 610, { fam: 'sans', size: 23, color: P.dim, a: np });
    }, () => {
      card(780, 340);
      eyebrow('THE PRODUCT', 26, 46, { size: 17 });
      txt('change is possible only if', 26, 96, { fam: 'sans', size: 24, color: P.dim });
      txt('OUT × INTACT × SIDEWAYS × UPWARD = 1', 26, 150, { fam: 'mono', size: 30, wt: 800, color: P.ink, maxW: 728 });
      txt('each test scores 0 or 1', 26, 214, { fam: 'sans', size: 24, color: P.ink, a: zp });
      rich([['0 × anything = 0', {}]], 26, 276, { size: 40, color: P.no, a: zp });
      txt('necessary, not sufficient', 754, 276, { fam: 'sans', size: 22, color: P.dim, align: 'right', a: np });
    });
  }

  function snrPanel(t, sc) {
    const N = snrN(t, sc);
    const l1 = [['x', {}], ['k', { sub: 1 }], [' = s + ε', {}], ['k', { sub: 1 }]];
    const l2 = [['x', { bar: 1 }], [' = s + ', {}], ['1', { it: false }], ['/', { it: false }], ['N', {}], [' Σ ε', {}], ['k', { sub: 1 }]];
    const l3 = [['noise ∝ 1/√', { it: false }], ['N', {}]];
    const l4 = [['SNR ∝ √', { it: false }], ['N', {}]];
    SIDE(() => {
      card(674, 680);
      eyebrow('THE MATH OF COMPARING NOTES', 32, 56, { maxW: 610 });
      rich(l1, 32, 134, { size: 46 });
      txt('each story = shared conditions + particulars', 32, 172, { fam: 'sans', size: 22, color: P.dim, maxW: 610 });
      rich(l2, 32, 254, { size: 46 });
      txt('average N stories: the particulars cancel', 32, 292, { fam: 'sans', size: 22, color: P.dim, maxW: 610 });
      rich(l3, 32, 370, { size: 40 });
      rich(l4, 32, 446, { size: 56, color: P.warm });
      ln(32, 488, 642, 488, P.rule, 1.5);
      [[1, '×1'], [16, '×4'], [256, '×16']].forEach(([n, s], i) => {
        const x = 32 + i * 207, on = N === n;
        box(x, 512, 196, 124, { r: 12, stroke: on ? P.warm : P.rule, lw: on ? 3 : 2, fill: on ? rgba(P.warm, 0.1) : null });
        txt('N = ' + n, x + 18, 554, { fam: 'mono', size: 20, color: P.dim });
        txt(s, x + 18, 612, { fam: 'mono', size: 40, wt: 800, color: on ? P.warm : P.ink });
      });
    }, () => {
      card(780, 340);
      eyebrow('THE MATH OF COMPARING NOTES', 26, 44, { size: 17 });
      rich(l1, 26, 106, { size: 38 });
      rich(l2, 26, 172, { size: 38 });
      rich(l4, 26, 250, { size: 44, color: P.warm });
      rich(l3, 440, 250, { size: 32 });
      txt('N = ' + N + '   clarity × ' + rootStr(N), 26, 306, { fam: 'mono', size: 22, wt: 700, color: P.ink });
    });
  }

  const MC = (() => {
    const r = rng(42), n = 1000, idx = {}, counts = [0, 0, 0, 0, 0, 0, 0], dots = [];
    BIN_ORDER.forEach((k, i) => { idx[k] = i; });
    for (let j = 0; j < n; j++) {
      const route = Math.floor(r() * 13), b = idx[HOPS[route].bin], slot = counts[b]++;
      dots.push({ b, slot, rel: 0.9 + (j / n) * 7.2 + r() * 0.15, jx: (r() - 0.5) * 40 });
    }
    return { dots, counts };
  })();
  function mcPanel(t) {
    const counts = [0, 0, 0, 0, 0, 0, 0];
    for (const d of MC.dots) if (t >= d.rel + 0.9) counts[d.b]++;
    const ks = { inward: 0, sealed: 0, sold: 0, bent: 0, unsent: 0, sideways: 0, delivered: 0 };
    HOPS.forEach((h) => { ks[h.bin]++; });
    SIDE(() => {
      card(674, 680);
      eyebrow('EXPECTED VS. OBSERVED', 32, 56);
      rich([['E', {}], ['[count] = n · k ÷ 13', { it: false }]], 32, 126, { size: 38 });
      txt('n = 1,000 people   k = routes that lead to the bin', 32, 166, { fam: 'sans', size: 21, color: P.dim, maxW: 610 });
      ['BIN', 'k', 'E', 'SEEN'].forEach((h, i) => txt(h, [32, 330, 450, 642][i], 224, { fam: 'mono', size: 15, wt: 700, color: P.faint, track: 2, align: i === 3 ? 'right' : i ? 'center' : 'left' }));
      ln(32, 240, 642, 240, P.rule, 1.5);
      BIN_ORDER.forEach((k, i) => {
        const y = 286 + i * 52, ex = Math.round((1000 * ks[k]) / 13);
        binIcon(k, 46, y - 8, 0.8, binColor(k));
        txt(BINS[k].name, 74, y, { fam: 'mono', size: 18, wt: 700, color: P.ink, track: 1.5 });
        txt(String(ks[k]), 330, y, { fam: 'mono', size: 21, color: P.dim, align: 'center' });
        txt(String(ex), 450, y, { fam: 'mono', size: 21, color: P.dim, align: 'center' });
        txt(String(counts[i]), 642, y, { fam: 'mono', size: 24, wt: 800, color: counts[i] ? P.ink : P.no, align: 'right' });
      });
    }, () => {
      card(780, 340);
      eyebrow('EXPECTED VS. OBSERVED · E = n·k ÷ 13', 26, 44, { size: 16, maxW: 728 });
      ['BIN', 'k', 'E', 'SEEN'].forEach((h, i) => txt(h, [26, 420, 560, 754][i], 82, { fam: 'mono', size: 15, wt: 700, color: P.faint, track: 2, align: i === 3 ? 'right' : i ? 'center' : 'left' }));
      BIN_ORDER.forEach((k, i) => {
        const y = 118 + i * 33, ex = Math.round((1000 * ks[k]) / 13);
        txt(BINS[k].name, 26, y, { fam: 'mono', size: 18, wt: 700, color: P.ink, track: 1 });
        txt(String(ks[k]), 420, y, { fam: 'mono', size: 19, color: P.dim, align: 'center' });
        txt(String(ex), 560, y, { fam: 'mono', size: 19, color: P.dim, align: 'center' });
        txt(String(counts[i]), 754, y, { fam: 'mono', size: 21, wt: 800, color: counts[i] ? P.ink : P.no, align: 'right' });
      });
    });
  }

  const POST = (() => {
    const r = rng(5), pts = [];
    while (pts.length < 46) {
      const x = 30 + r() * 940, y = 30 + r() * 620;
      if (Math.abs(x - 500) < 150 && y > 160 && y < 560) continue;
      if (Math.hypot(x - 210, y - 400) < 110 || Math.hypot(x - 790, y - 400) < 110) continue;
      pts.push({ x, y, c: r() < 0.32, ph: r() });
    }
    return pts;
  })();
  const POST_V = 280;
  const postStart = (sc) => sc.B[1] + 1.2;
  function postLit(t, sc) {
    const bt = postStart(sc);
    return POST.filter((n) => t >= bt + Math.hypot(n.x - 500, n.y - 220) / POST_V).length;
  }
  function journalIcon(x, y, a) {
    ctx.save();
    ctx.globalAlpha *= a;
    box(x - 60, y - 76, 120, 152, { r: 10, stroke: P.dead, lw: 2.5 });
    for (let k = 0; k < 6; k++) dot(x - 60, y - 60 + k * 24, 5, P.bg, P.dead, 2);
    for (let k = 0; k < 5; k++) ln(x - 40, y - 46 + k * 24, x + 44, y - 46 + k * 24, P.rule, 1.5);
    txt('JOURNAL', x, y + 112, { fam: 'mono', size: 16, color: P.dim, align: 'center', track: 2 });
    ctx.restore();
  }
  function fileIcon(x, y, a) {
    ctx.save();
    ctx.globalAlpha *= a;
    box(x - 66, y - 80, 132, 160, { r: 8, stroke: P.dead, lw: 2.5 });
    ln(x - 66, y - 26, x + 66, y - 26, P.dead, 2);
    ln(x - 66, y + 28, x + 66, y + 28, P.dead, 2);
    [-53, 1, 55].forEach((dy) => box(x - 18, y + dy - 6, 36, 8, { r: 3, fill: P.dead }));
    binIcon('sealed', x + 46, y - 62, 0.7, P.dead);
    txt('THERAPIST’S FILE', x, y + 112, { fam: 'mono', size: 16, color: P.dim, align: 'center', track: 2 });
    ctx.restore();
  }
  function postPanel(t, sc) {
    const n = postLit(t, sc), B1 = sc.B[1];
    const lines = [['$ post --public', P.dim], ['payload    8 of 8 fields', P.ink], ['dst        anyone who can receive it', P.ink], ['received   ' + n + ' people so far', n ? P.warm : P.ink], ['replies    “me too”', P.ink]];
    const lp = (i) => seg(t, 0.8 + i * 0.5, 1.2 + i * 0.5, E.lin);
    const cl = seg(t, B1 + 0.4, B1 + 1.0, E.lin);
    SIDE(() => {
      card(674, 680);
      eyebrow('BROADCAST', 32, 56);
      lines.forEach(([s, c], i) => txt(s, 32, 132 + i * 64, { fam: 'mono', size: 21, wt: i === 3 ? 800 : 500, color: c, maxW: 610, a: lp(i) }));
      ln(32, 460, 642, 460, P.rule, 1.5);
      para('From a dead end to a broadcast.', 32, 530, 610, { fam: 'serif', it: true, size: 44, color: P.warm, a: cl, lh: 1.15 });
    }, () => {
      card(780, 340);
      eyebrow('BROADCAST', 26, 44, { size: 17 });
      lines.forEach(([s, c], i) => txt(s, 26, 94 + i * 46, { fam: 'mono', size: 20, wt: i === 3 ? 800 : 500, color: c, maxW: 728, a: lp(i) }));
      txt('From a dead end to a broadcast.', 26, 318, { fam: 'serif', it: true, size: 32, color: P.warm, a: cl });
    });
  }

  /* ================= header strip: the 13 routes so far ================= */
  function drawStrip(gt, sc) {
    const lnd = land(), hd = L.header, step = lnd ? 40 : 72, w = lnd ? 30 : 44;
    const x0 = lnd ? hd.x + hd.w - 12 * step - w : hd.x, y = lnd ? hd.y + 38 : hd.y + 166;
    HOPS.forEach((h, i) => {
      const cx = x0 + i * step + w / 2, done = h.doneAt != null && gt >= h.doneAt, cur = sc.hop === h && !done;
      if (done) packet(cx, y, w, { header: false, stroke: P.dead, cellColor: P.dead, fill: P.bg });
      else if (cur) packet(cx, y, w, { header: false, glow: 0.5 + 0.5 * Math.sin(gt * 5) });
      else packet(cx, y, w, { header: false, stroke: P.rule, cellColor: P.rule, fill: P.bg });
    });
  }

  /* ================= scenes ================= */
  function terminal(x, y, t, size) {
    const w = txt('$ traceroute --payload=need conditions', x, y, { fam: 'mono', size, wt: 500, color: P.dim });
    if (Math.floor(t * 2) % 2 === 0) box(x + w + 8, y - size * 0.85, size * 0.6, size, { r: 2, fill: P.warm });
  }
  function drawTitle(t) {
    const pulse = 0.8 + 0.25 * Math.sin(t * 2.2);
    const sub = 'One human need, traced hop by hop through the societal machine, to see who ever receives it.';
    if (land()) {
      eyebrow('AN ANIMATED TRACE', 96, 300, { size: 22 });
      txt('PACKET LOSS', 90, 450, { fam: 'mono', size: 150, wt: 800, color: P.ink, maxW: 1180 });
      para(sub, 96, 540, 1060, { fam: 'serif', it: true, size: 44, color: P.dim, lh: 1.25 });
      terminal(96, 720, t, 28);
      person(1580, 690, 2.2, { color: P.warm });
      packet(1580, 420, 280, { glow: pulse, dst: 'whoever controls the conditions' });
    } else {
      eyebrow('AN ANIMATED TRACE', 64, 270, { size: 26 });
      txt('PACKET', 58, 420, { fam: 'mono', size: 160, wt: 800, color: P.ink, maxW: 960 });
      txt('LOSS', 58, 580, { fam: 'mono', size: 160, wt: 800, color: P.ink, maxW: 960 });
      para(sub, 64, 670, 952, { fam: 'serif', it: true, size: 46, color: P.dim, lh: 1.25 });
      terminal(64, 890, t, 26);
      const room = L.cap.y - 40 - 940, cy = 940 + room * 0.62;
      packet(540, cy - 170 * Math.min(1, room / 380), 260, { glow: pulse, dst: 'whoever controls the conditions' });
      person(540, cy + 40, 1.6, { color: P.warm });
    }
  }

  function cellCard(x, y, w, h, title, sub, col, p, idx, letter) {
    if (p <= 0) { box(x, y, w, h, { r: 14, stroke: P.rule, lw: 2, dash: [6, 6] }); return; }
    ctx.save();
    ctx.globalAlpha *= clamp(p * 1.4);
    ctx.translate(0, (1 - p) * 18);
    box(x, y, w, h, { r: 14, fill: rgba(col, 0.14), stroke: col, lw: 2.5 });
    rich([[letter, {}], [String(idx), { sub: 1 }]], x + 18, y + 40, { size: 30, color: col });
    txt(title, x + 18, y + h * 0.56, { fam: 'sans', wt: 700, size: 30, color: P.ink, maxW: w - 34, min: 20 });
    para(sub, x + 18, y + h * 0.56 + 34, w - 34, { fam: 'sans', size: 21, color: P.dim, lh: 1.22 });
    ctx.restore();
  }
  function drawPacketScene(t, sc) {
    const B1 = sc.B[1];
    MAIN(() => {
      const x = 30, y = 40, w = 940, h = 590;
      ctx.save();
      ctx.shadowColor = rgba(P.warm, 0.3);
      ctx.shadowBlur = 40 * X.curScale();
      box(x, y, w, h, { r: 24, fill: P.raise });
      ctx.restore();
      box(x, y, w, h, { r: 24, stroke: P.warm, lw: 3 });
      ln(x + 20, y + 116, x + w - 20, y + 116, rgba(P.warm, 0.5), 2);
      let hx = x + 30;
      [['SRC', 'one person', 190], ['DST', 'whoever controls the conditions', 440], ['TYPE', 'need', 140], ['TTL', 'until met', 150]].forEach(([k, v, cw], i) => {
        const p = seg(t, 0.5 + i * 0.35, 0.9 + i * 0.35, E.lin);
        txt(k, hx, y + 48, { fam: 'mono', size: 16, color: P.faint, track: 2, a: p });
        txt(v, hx, y + 88, { fam: 'sans', size: 27, wt: 700, color: P.ink, a: p, maxW: cw - 20, min: 18 });
        hx += cw;
      });
      txt('PAYLOAD · 8 FIELDS', x + 30, y + 162, { fam: 'mono', size: 16, color: P.faint, track: 2 });
      const nw = (w - 60 - 32) / 3;
      [['connection', 'deeper, more meaningful'], ['a village', 'community, belonging'], ['growth', 'spiritual and emotional']].forEach(([a, b], i) =>
        cellCard(x + 30 + i * (nw + 16), y + 184, nw, 150, a, b, P.gold, seg(t, 1.8 + i * 0.7, 2.4 + i * 0.7, E.out), i + 1, 'n'));
      const cw2 = (w - 60 - 56) / 5;
      [['isolation', 'alone most days'], ['overwork', 'work or perish'], ['rent', 'takes most of the pay'], ['food', 'never quite secure'], ['abuse', 'of power, from above']].forEach(([a, b], i) =>
        cellCard(x + 30 + i * (cw2 + 14), y + 352, cw2, 200, a, b, P.warm, seg(t, B1 + 0.4 + i * 0.6, B1 + 1.0 + i * 0.6, E.out), i + 1, 'c'));
    });
    vectorPanel(t, sc);
  }

  function drawTest(t, sc) {
    const B0 = sc.B[0], B1 = sc.B[1], B2 = sc.B[2], B3 = sc.B[3];
    const reveal = [B0 + 2.2, B0 + 5.0, B1 + 0.6, B1 + 3.8];
    const flipped = t >= B2 + 1.4 && t < B3 - 0.4;
    MAIN(() => {
      const rows = [['OUT', 'it gets out of you'], ['INTACT', 'its meaning survives the trip'], ['SIDEWAYS', 'it reaches others in the same situation'], ['UPWARD', 'it reaches whoever controls the conditions']];
      const gx = 790, gy = 330;
      let allOn = true;
      rows.forEach(([k, d], i) => {
        const y = 100 + i * 150, p = seg(t, reveal[i], reveal[i] + 0.6, E.out);
        if (p <= 0) allOn = false;
        const v = i === 2 && flipped ? 0 : 1, col = p <= 0 ? P.rule : v ? P.yes : P.no;
        txt(k, 30, y, { fam: 'mono', size: 30, wt: 800, color: P.ink, track: 2, a: 0.25 + 0.75 * p });
        txt(d, 30, y + 42, { fam: 'sans', size: 27, color: P.dim, a: p, maxW: 560 });
        const iy = gy - 96 + i * 64;
        polyPath([[668, y - 10], [712, y - 10], [712, iy], [gx - 60, iy]], 1, col, 3);
        box(616, y - 36, 50, 50, { r: 10, stroke: col, lw: 2, fill: p > 0 ? rgba(col, 0.12) : null });
        txt(p > 0 ? String(v) : '–', 641, y + 1, { fam: 'mono', size: 30, wt: 800, color: p > 0 ? col : P.faint, align: 'center' });
      });
      const out = allOn && !flipped ? 1 : 0;
      ctx.beginPath();
      ctx.moveTo(gx - 60, gy - 130);
      ctx.lineTo(gx, gy - 130);
      ctx.arc(gx, gy, 130, -Math.PI / 2, Math.PI / 2);
      ctx.lineTo(gx - 60, gy + 130);
      ctx.closePath();
      ctx.fillStyle = rgba(P.raise, 0.95);
      ctx.fill();
      ctx.strokeStyle = P.lineHi;
      ctx.lineWidth = 3;
      ctx.stroke();
      txt('×', gx + 10, gy + 24, { fam: 'serif', size: 76, color: P.ink, align: 'center' });
      const oc = allOn ? (out ? P.yes : P.no) : P.rule;
      ln(gx + 130, gy, 990, gy, oc, 4);
      txt(allOn ? String(out) : '–', 958, gy - 18, { fam: 'mono', size: 34, wt: 800, color: oc, align: 'center' });
      txt('CHANGE', 990, gy + 94, { fam: 'mono', size: 15, wt: 700, color: P.dim, align: 'right', track: 2 });
      txt('POSSIBLE', 990, gy + 116, { fam: 'mono', size: 15, wt: 700, color: P.dim, align: 'right', track: 2 });
    });
    equationPanel(t, sc);
  }

  function drawMachine(t, sc, gt) {
    MAIN(() => {
      person(64, 360, 0.8, { label: 'YOU', labelSize: 16 });
      const tr = seg(t, 0.4, 1.4);
      if (tr < 1) packet(lerp(110, 165, tr), lerp(300, 340, tr), 46, { header: false, glow: 0.7 });
      box(130, 30, 72, 620, { r: 14, stroke: P.lineHi, lw: 2.5, fill: rgba(P.raise, 0.85) });
      ctx.save();
      ctx.translate(166, 340);
      ctx.rotate(-Math.PI / 2);
      txt('STANDARD ADVICE', 0, 7, { fam: 'mono', size: 18, wt: 700, color: P.dim, align: 'center', track: 4 });
      ctx.restore();
      HOPS.forEach((h, i) => {
        const y = 60 + i * 47.5, p = seg(t, 1.5 + i * 0.1, 2.2 + i * 0.1, E.out);
        ln(202, y, 202 + 50 * p, y, P.line, 2);
        const w = txt(h.route, 266, y + 9, { fam: 'sans', size: 26, color: P.ink, a: p });
        const x0 = 266 + w + 16;
        if (p > 0) ln(x0, y, 920, y, rgba(P.line, p), 1.5, [3, 9]);
        txt('?', 952, y + 10, { fam: 'mono', size: 26, wt: 800, color: P.faint, align: 'center', a: p });
        const pk = seg(t, 2.6 + i * 0.12, 4.4 + i * 0.12, E.io);
        if (pk > 0 && pk < 1) packet(lerp(x0, 920, pk), y, 32, { header: false, a: 1 - pk * 0.4 });
      });
    });
    legendPanel(t);
    drawStrip(gt, sc);
  }

  function drawHop(t, sc, gt) {
    const h = sc.hop;
    MAIN(() => h.draw(t, sc));
    reportSide(h, t, sc);
    drawStrip(gt, sc);
  }

  function drawPattern(t, sc, gt) {
    const B1 = sc.B[1], B2 = sc.B[2];
    MAIN(() => {
      const cols = [470, 590, 720, 850], pc = 950;
      txt('ROUTE', 20, 34, { fam: 'sans', wt: 700, size: 18, color: P.dim, track: 1.2 });
      X.GATES.forEach((g, i) => txt(g, cols[i], 34, { fam: 'sans', wt: 700, size: 18, color: P.dim, align: 'center', track: 1.2 }));
      txt('=', pc, 36, { fam: 'serif', size: 30, color: P.dim, align: 'center' });
      ln(0, 52, 1000, 52, P.rule, 1.5);
      HOPS.forEach((h, i) => {
        const y = 92 + i * 45.5, p = seg(t, 0.4 + i * 0.2, 0.8 + i * 0.2, E.out);
        if (p <= 0) return;
        ctx.save();
        ctx.globalAlpha *= p;
        txt(h.name, 20, y, { fam: 'sans', size: 27, wt: 700, color: P.ink });
        h.gates.forEach((v, j) => txt(String(v), cols[j], y, { fam: 'mono', size: 27, wt: 800, color: v ? P.yes : P.no, align: 'center' }));
        txt('0', pc, y, { fam: 'mono', size: 29, wt: 800, color: P.no, align: 'center' });
        ctx.restore();
      });
      const top = 60, hgt = 13 * 45.5 + 4;
      const hp = seg(t, B1 - 0.6, B1, E.lin);
      if (hp > 0) box(pc - 36, top, 72, hgt, { r: 12, stroke: rgba(P.no, hp), lw: 3 });
      const bp = seg(t, B1 + 3.2, B1 + 3.8, E.lin);
      if (bp > 0) [10, 11].forEach((i) => ring(cols[3], 92 + i * 45.5 - 10, 24, bp, P.power, 3));
      const sp = seg(t, B2 + 0.2, B2 + 0.8, E.lin);
      if (sp > 0) box(cols[2] - 62, top, 124, hgt, { r: 12, stroke: rgba(P.warm, sp), lw: 3, dash: [8, 6] });
    });
    const k = seg(t, 0.4, 3.2, E.lin), c = { inward: 0, sealed: 0, sold: 0, bent: 0, unsent: 0, sideways: 0, delivered: 0 };
    HOPS.forEach((h) => { c[h.bin] += k; });
    binsPanel(c, t, 'WHERE THE 13 PACKETS LANDED', { pulse: ['sideways', 'delivered'], pulseA: seg(t, B2, B2 + 0.6, E.lin) });
    drawStrip(gt, sc);
  }

  function drawScale(t, sc) {
    const B0 = sc.B[0];
    MAIN(() => {
      const cxs = (k) => 76 + k * 141, by = 600, top = 300;
      dot(500, 64, 26, rgba(P.warm, 0.15), P.warm, 2.5);
      txt('1,000 PEOPLE', 542, 56, { fam: 'mono', size: 16, wt: 700, color: P.dim, track: 2 });
      txt('each takes one of the 13 routes', 542, 84, { fam: 'sans', size: 20, color: P.dim });
      const shown = [0, 0, 0, 0, 0, 0, 0];
      for (const d of MC.dots) {
        if (t < d.rel) continue;
        const p = clamp((t - d.rel) / 0.9), col = d.slot % 16, row = (d.slot / 16) | 0;
        const tx = cxs(d.b) - 56 + col * 7.4, ty = by - 8 - row * 7;
        if (p >= 1) { shown[d.b]++; dot(tx, ty, 2.7, P.dead); }
        else { const q = quad([500, 70], [lerp(500, tx, 0.5) + d.jx, 150], [tx, ty], E.in(p)); dot(q[0], q[1], 3, P.warm); }
      }
      BIN_ORDER.forEach((k, i) => {
        const x = cxs(i);
        ctx.beginPath();
        ctx.moveTo(x - 64, top);
        ctx.lineTo(x - 64, by);
        ctx.lineTo(x + 64, by);
        ctx.lineTo(x + 64, top);
        ctx.strokeStyle = binColor(k);
        ctx.lineWidth = 2.5;
        ctx.stroke();
        txt(BINS[k].name, x, by + 38, { fam: 'sans', size: 21, wt: 700, color: P.ink, align: 'center', track: 1, maxW: 134 });
        txt(String(shown[i]), x, top - 16, { fam: 'mono', size: 28, wt: 800, color: shown[i] ? P.ink : P.no, align: 'center' });
      });
      const em = seg(t, B0 + 4.5, B0 + 5.2, E.lin);
      if (em > 0) [5, 6].forEach((i) => box(cxs(i) - 70, top - 54, 140, by - top + 104, { r: 12, stroke: rgba(i === 6 ? P.yes : P.warm, em * (0.6 + 0.4 * Math.sin(t * 5))), lw: 3, dash: [8, 6] }));
    });
    mcPanel(t);
  }

  function drawOut(t, sc) {
    const o = sc.out;
    MAIN(() => o.draw(t, sc));
    if (o.side === 'snr') snrPanel(t, sc); else reportSide(o, t, sc);
  }

  function drawCompare(t) {
    const sums = [0, 1, 2, 3].map((j) => HOPS.reduce((a, h) => a + h.gates[j], 0));
    MAIN(() => {
      const cols = [480, 600, 730, 860], pc = 955;
      txt('ROUTE', 20, 38, { fam: 'sans', wt: 700, size: 18, color: P.dim, track: 1.2 });
      X.GATES.forEach((g, i) => txt(g, cols[i], 38, { fam: 'sans', wt: 700, size: 18, color: P.dim, align: 'center', track: 1.2 }));
      txt('=', pc, 40, { fam: 'serif', size: 30, color: P.dim, align: 'center' });
      ln(0, 58, 1000, 58, P.rule, 1.5);
      const p0 = seg(t, 0.4, 1.0, E.out);
      ctx.save();
      ctx.globalAlpha *= p0;
      txt('13 standard routes', 20, 112, { fam: 'sans', size: 28, wt: 700, color: P.ink });
      txt('column totals', 20, 144, { fam: 'sans', size: 19, color: P.dim });
      sums.forEach((v, j) => txt(v + '/13', cols[j], 116, { fam: 'mono', size: 23, wt: 800, color: v ? P.ink : P.no, align: 'center' }));
      txt('0/13', pc, 116, { fam: 'mono', size: 23, wt: 800, color: P.no, align: 'center' });
      ctx.restore();
      ln(0, 176, 1000, 176, P.rule, 1.5);
      OUTS.forEach((o, i) => {
        const y = 232 + i * 74, p = seg(t, 1.4 + i * 0.6, 1.9 + i * 0.6, E.out);
        if (p <= 0) return;
        ctx.save();
        ctx.globalAlpha *= p;
        txt(o.name, 20, y, { fam: 'sans', size: 28, wt: 700, color: P.ink });
        o.gates.forEach((v, j) => txt(String(v), cols[j], y, { fam: 'mono', size: 28, wt: 800, color: v ? P.yes : P.no, align: 'center' }));
        const prod = o.gates.every(Boolean) ? 1 : 0, col = prod ? P.yes : P.no;
        box(pc - 26, y - 34, 52, 46, { r: 10, stroke: col, lw: 2.5, fill: rgba(col, 0.12) });
        txt(String(prod), pc, y, { fam: 'mono', size: 28, wt: 800, color: col, align: 'center' });
        ctx.restore();
      });
      const sp = seg(t, 1.6, 2.2, E.lin);
      if (sp > 0) ring(cols[2], 108, 40, sp, P.no, 3);
      const st = seg(t, 4.8, 5.4, E.lin);
      if (st > 0) para('The outward routes stack. Telling, comparing and naming supply the terms that organizing delivers.', 20, 626, 960, { fam: 'sans', size: 24, color: P.dim, a: st });
    });
    const c = { inward: 0, sealed: 0, sold: 0, bent: 0, unsent: 0, sideways: 0, delivered: 0 };
    HOPS.forEach((h) => { c[h.bin] += 1; });
    c.sideways = 3 * seg(t, 1.4, 3.2, E.lin);
    c.delivered = 2 * seg(t, 3.2, 4.4, E.lin);
    binsPanel(c, t, 'WHERE ALL 18 PACKETS LANDED', { pulse: ['sideways', 'delivered'], pulseA: seg(t, 4.4, 5.0, E.lin) });
  }

  function drawPost(t, sc) {
    const B1 = sc.B[1];
    MAIN(() => {
      const fade = 1 - 0.65 * seg(t, B1 - 0.4, B1 + 0.6, E.lin);
      journalIcon(210, 400, fade);
      fileIcon(790, 400, fade);
      person(500, 420, 1, { label: 'YOU' });
      const a1 = seg(t, 1.0, 2.0) - seg(t, 2.2, 3.0), a2 = seg(t, 3.4, 4.4) - seg(t, 4.6, 5.4), up = seg(t, B1 + 0.2, B1 + 1.2);
      const px = 500 - 170 * a1 + 170 * a2, py = 300 - 80 * up, bt = postStart(sc);
      for (let k = 0; k < 4; k++) {
        const st = bt + k * 1.1;
        if (t < st) continue;
        const R = (t - st) * POST_V;
        if (R < 760) ring(px, py, R, 0.75 * (1 - R / 760), P.warm, 3);
      }
      POST.forEach((n) => {
        const hit = bt + Math.hypot(n.x - 500, n.y - 220) / POST_V, l = seg(t, hit, hit + 0.4, E.lin);
        dot(n.x, n.y, 10, l > 0 ? rgba(P.warm, 0.25 + 0.6 * l) : null, l > 0 ? P.warm : P.dead, 2);
        if (n.c && t > hit + 0.7) { const age = (t - hit - 0.7 + n.ph * 1.6) % 1.6; ring(n.x, n.y, 12 + age * 70, 0.55 * (1 - age / 1.6), P.warm, 2); }
      });
      packet(px, py, 130, { glow: 1, dst: up > 0.5 ? 'anyone who can receive it' : '?' });
    });
    postPanel(t, sc);
  }

  function drawEnd(t) {
    const W = X.W(), lnd = land(), cx = W / 2, mw = W - 160;
    const a1 = seg(t, 0.2, 1.0, E.lin), a2 = seg(t, 1.0, 1.8, E.lin), a3 = seg(t, 1.9, 2.7, E.lin);
    const y0 = lnd ? 300 : 520;
    txt('--- conditions ping statistics ---', cx, y0, { fam: 'mono', size: 28, color: P.dim, align: 'center', a: a1, maxW: mw });
    if (lnd) txt('13 packets transmitted, 0 received, 100% packet loss', cx, y0 + 62, { fam: 'mono', size: 34, wt: 800, color: P.ink, align: 'center', a: a1, maxW: mw });
    else {
      txt('13 packets transmitted, 0 received,', cx, y0 + 62, { fam: 'mono', size: 30, wt: 800, color: P.ink, align: 'center', a: a1, maxW: mw });
      txt('100% packet loss', cx, y0 + 108, { fam: 'mono', size: 30, wt: 800, color: P.ink, align: 'center', a: a1, maxW: mw });
    }
    const dy = lnd ? 0 : 46;
    txt('received = got out, intact, sideways and upward', cx, y0 + 112 + dy, { fam: 'sans', size: 28, color: P.dim, align: 'center', a: a1, maxW: mw });
    txt('PACKET LOSS', cx, y0 + 330 + dy, { fam: 'mono', size: lnd ? 140 : 118, wt: 800, color: P.ink, align: 'center', a: a2, maxW: mw });
    txt('Send it where it can be received.', cx, y0 + 430 + dy, { fam: 'serif', it: true, size: lnd ? 54 : 50, color: P.warm, align: 'center', a: a3, maxW: mw });
    const pulse = 0.6 + 0.3 * Math.sin(t * 2.4);
    packet(cx, y0 + 560 + dy, 120, { glow: pulse * a3, a: a3, dst: 'anyone' });
  }

  /* ================= the timeline ================= */
  const SCENES = [
    {
      id: 'title', header: false, lead: 1.6, chapter: 'Title', tick: true, draw: drawTitle,
      beats: ['Treat a person’s suffering as information: a report on the conditions they’re living in. Then follow it, and see who receives it.'],
    },
    {
      id: 'packet', eyebrow: 'THE PACKET', title: 'One need, eight fields', chapter: 'The packet', tick: true, draw: drawPacketScene,
      beats: [
        'Every packet starts with a person who needs something: deeper connection, a community, a village, room to grow emotionally and spiritually.',
        'It also carries data about the conditions that produced the need: isolation, work-or-perish hours, rent, food, and someone above them abusing power.',
      ],
    },
    {
      id: 'test', eyebrow: 'THE TEST', title: 'Four conditions for change', chapter: 'The test', tick: true, draw: drawTest,
      beats: [
        'For the information to change anything, four things have to be true. It has to get out of you, and arrive with its meaning intact.',
        'It has to travel sideways, to others in the same situation, and upward, to whoever controls housing, wages, food and the work-or-perish arrangement.',
        'Score each test 0 or 1 and multiply. A single zero makes the product zero.',
        'None of this judges whether a practice helps you feel better. It asks a narrower question: where does the information go?',
      ],
    },
    {
      id: 'machine', eyebrow: 'THE MACHINE', title: 'The standard advice catalog', chapter: 'The machine', tick: true, strip: true, draw: drawMachine,
      beats: [
        'Here are thirteen things people are routinely told to do with their pain. Each one is a route the packet can take.',
        'We’ll send the packet down every route and read the delivery report at the other end.',
      ],
    },
  ];
  HOPS.forEach((h, i) => SCENES.push({ id: h.id, eyebrow: 'ROUTE ' + pad2(i + 1) + ' OF 13', title: h.title, chapter: 'Route ' + (i + 1) + ': ' + h.name, tick: true, strip: true, hop: h, beats: h.beats, draw: drawHop }));
  SCENES.push(
    {
      id: 'pattern', eyebrow: 'THE PATTERN', title: 'Thirteen routes, thirteen zeros', chapter: 'The pattern', tick: true, strip: true, draw: drawPattern,
      beats: [
        'Seen side by side, the pattern looks almost designed.',
        'Every route sends the pain inward, into a sealed box, or to a profit-taker. The two that reach power bend the signal or crush it.',
        'None of the thirteen sends it sideways, to people suffering the same way, or upward with its meaning intact.',
      ],
    },
    {
      id: 'scale', eyebrow: 'AT SCALE', title: 'A thousand people take the advice', chapter: 'At scale', tick: true, minDur: 14, draw: drawScale,
      beats: [
        'Run the catalog for a thousand people. The totals grow, and the two bins that matter stay empty.',
        'Whether someone engineered it or it grew out of the incentives, the effect protects the arrangement.',
        'A society that wanted conditions to stay the same couldn’t design a better catalog than one that tells every suffering person to handle it privately.',
      ],
    },
  );
  OUTS.forEach((o, i) => SCENES.push({ id: o.id, eyebrow: 'OUTWARD ' + (i + 1) + ' OF 5', title: o.title, chapter: 'Outward ' + (i + 1) + ': ' + o.name, tick: true, out: o, beats: o.beats, minDur: o.minDur, draw: drawOut }));
  SCENES.push(
    {
      id: 'compare', eyebrow: 'SIDE BY SIDE', title: 'Where each kind of route leads', chapter: 'Side by side', tick: true, draw: drawCompare,
      beats: [
        'Put the two lists side by side. The thirteen standard routes never send anything sideways. The outward routes stack, each supplying a term the next one needs.',
        'Those are the channels society almost never recommends, which tells you something about who benefits from the ones it does.',
      ],
    },
    {
      id: 'post', eyebrow: 'BROADCAST', title: 'When you post', chapter: 'Broadcast', tick: true, tail: 2.5, draw: drawPost,
      beats: [
        'That’s also what you’re doing when you post. What would have gone into a journal or a therapist’s file goes where other people can receive it.',
        'You’re turning a dead-end signal into a broadcast.',
      ],
    },
    { id: 'end', header: false, chapter: 'End', lead: 0, tail: 0, beats: [{ text: '', dur: 7.5 }], draw: drawEnd },
  );

  /* ================= page: ledger + narration ================= */
  function buildLedger() {
    const tb = document.getElementById('ledger-body');
    if (!tb) return;
    tb.innerHTML = '';
    const group = (label) => {
      const tr = document.createElement('tr');
      tr.className = 'group';
      tr.innerHTML = '<td colspan="8">' + esc(label) + '</td>';
      tb.appendChild(tr);
    };
    const row = (d) => {
      const tr = document.createElement('tr'), prod = d.gates.every(Boolean) ? 1 : 0;
      tr.innerHTML = '<th scope="row" class="route">' + esc(d.name) + '</th><td class="where">' + esc(d.where) + '</td>' +
        d.gates.map((v) => '<td class="bit ' + (v ? 'one' : 'zero') + '">' + v + '</td>').join('') +
        '<td class="bit prod ' + (prod ? 'one' : 'zero') + '"><b>' + prod + '</b></td>' +
        '<td><span class="binchip ' + d.bin + '">' + BINS[d.bin].name + '</span></td>';
      tb.appendChild(tr);
    };
    group('The standard advice · 13 routes');
    HOPS.forEach(row);
    group('Outward channels · 5 routes');
    OUTS.forEach(row);
  }
  function buildTranscript() {
    const ol = document.getElementById('transcript-list');
    if (!ol) return;
    ol.innerHTML = '';
    SCENES.forEach((sc) => {
      const texts = sc.beats.map((b) => b.text).filter(Boolean);
      if (!texts.length) return;
      const li = document.createElement('li');
      li.innerHTML = '<h3>' + esc(sc.eyebrow || 'OPENING') + ' · ' + X.fmt(sc.start) + '</h3>' + (sc.title ? '<p class="q">' + esc(sc.title) + '</p>' : '') + texts.map((s) => '<p>' + esc(s) + '</p>').join('');
      ol.appendChild(li);
    });
  }

  X.onBuilt = function (scenes, total) {
    scenes.forEach((sc) => { if (sc.hop) sc.hop.doneAt = sc.start + sc.dur * 0.74 + 0.35; });
    buildLedger();
    buildTranscript();
    const rt = document.getElementById('runtime');
    if (rt) rt.textContent = Math.round(total / 60) + ' minutes';
  };
  X.DATA = { HOPS, OUTS, BINS };
  X.start(SCENES);
})();
