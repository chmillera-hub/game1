/* Packet Received · core.js
   Pure game logic: options, the lens math, month events and resolution.
   Runs in the browser (window.PacketCore) and in Node (module.exports) so the
   balance can be simulated. No DOM access in this file. */
(function (root) {
  'use strict';

  const N = 1000;         // people in town
  const MONTHS_TOTAL = 12;
  const ENERGY_MAX = 10;
  const ENERGY_START = 8;
  const DRAIN = 2;        // work or perish, every month after the first
  const COVER_AT = 20;    // with this many carriers, people cover for you and the drain drops by 1
  const GENERATIONS = 2;  // you → receivers → their contacts → theirs

  function rng(seed) {
    let s = seed >>> 0;
    return function () {
      s = (s + 0x6d2b79f5) >>> 0;
      let t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* k may depend on the state (network effects). kText explains it. */
  const OPTIONS = {
    /* ---------- the standard advice ---------- */
    gym: {
      kind: 'standard', title: 'Go to the gym', from: 'your doctor', receiver: 'your muscles',
      k: 0, energy: 3, side: 0, up: 0, bin: 'inward', fate: 'ABSORBED', becomes: 'endurance',
      why: 'The signal goes into your muscles. You can endure more, and nobody learns why you needed to.',
    },
    therapy: {
      kind: 'standard', title: 'Try therapy', from: 'a friend who means well', receiver: 'one professional',
      k: 1, phi: 1, R0: 0, energy: 3, side: 0, up: 0, bin: 'sealed', fate: 'SEALED', becomes: 'a confidential file',
      why: 'Heard in full by one person, then sealed. Confidentiality protects you, and it also sets the forward rate to zero.',
    },
    journal: {
      kind: 'standard', keep: 1, title: 'Journal about it', from: 'a wellness app', receiver: 'you, at 127.0.0.1',
      k: 0, energy: 1, fields: 1, side: 0, up: 0, bin: 'inward', fate: 'LOOPBACK', becomes: 'a clearer packet, addressed to yourself',
      why: 'Writing it down sharpens the message (+1 field). The only reader is you.',
    },
    meditate: {
      kind: 'standard', title: 'Meditate. Breathe.', from: 'the wellness email', receiver: 'your nervous system',
      k: 0, energy: 2, side: 0, up: 0, bin: 'inward', fate: 'MUTED', becomes: 'a quieter alarm',
      why: 'You feel the alarm less. The conditions that set it off are unchanged.',
    },
    hobby: {
      kind: 'standard', title: 'Get a hobby', from: 'your mom', receiver: 'an activity',
      k: 0, energy: 2, side: 0, up: 0, bin: 'inward', fate: 'DIVERTED', becomes: 'spent energy',
      why: 'Three people in the room, zero informed. Bringing it up would break the frame.',
    },
    selfcare: {
      kind: 'standard', title: 'Treat yourself', from: 'an ad', receiver: 'a retailer',
      k: 0, energy: 1, out: 1, side: 0, up: 0, bin: 'sold', fate: 'SOLD', becomes: 'a sales record',
      why: 'The only one who learns anything is a retailer, and what it learns is that sad people buy candles.',
    },
    gratitude: {
      kind: 'standard', title: 'Practice gratitude', from: 'a poster in the break room', receiver: 'no one',
      k: 0, energy: 2, fields: -1, side: 0, up: 0, bin: 'inward', fate: 'OVERWRITTEN', becomes: '“I’m grateful for what I have.”',
      why: 'One field of your payload is rewritten before it ever leaves (−1 field).',
    },
    meds: {
      kind: 'standard', title: 'Ask about medication', from: 'your doctor', receiver: 'a prescriber',
      k: 1, phi: 0.125, R0: 0, energy: 2, side: 0, up: 0, bin: 'sealed', fate: 'RECODED', becomes: 'a diagnosis code',
      why: 'It can genuinely help you get through. The record says “brain,” not “conditions,” and nobody forwards a claim form.',
    },
    apps: {
      kind: 'standard', keep: 1, title: 'Try the dating apps', from: 'everyone', receiver: 'an app company',
      k: 0, energy: -1, out: 1, side: 0, up: 0, bin: 'sold', fate: 'CAPTURED', becomes: 'a retention metric',
      why: 'The algorithm learns you; no human does. A solved user is a lost subscriber.',
    },
    selfhelp: {
      kind: 'standard', keep: 1, title: 'Read the self-help book', from: 'an influencer', receiver: 'no one: it only flows to you',
      k: 0, energy: 1, side: 0, up: 0, bin: 'sold', fate: 'ONE-WAY', becomes: 'a bigger audience for them',
      why: 'Their words reach you. Yours reach no one.',
    },
    hr: {
      kind: 'standard', title: 'Go to HR', from: 'a coworker', receiver: 'the institution',
      k: 2, phi: 0.25, R0: 0, energy: -1, side: 0, up: 1, bin: 'bent', fate: 'LIABILITY', becomes: 'a risk file',
      risk: { p: 0.3, label: 'retaliation', energy: -2 },
      why: 'It reaches power, relabeled as liability, and nobody there passes it on.',
    },
    vote: {
      kind: 'standard', title: 'Just vote', from: 'every channel', receiver: 'a tally',
      k: 0, energy: -1, out: 1, side: 0, up: 1, bin: 'bent', fate: 'COMPRESSED', becomes: 'one bit', election: true,
      why: 'It reaches power as at most one bit: log₂ 2 = 1. No human learns your conditions.',
    },
    private: {
      kind: 'standard', keep: 1, title: 'Keep it private', from: 'your family', receiver: 'nobody',
      k: 0, energy: 0, side: 0, up: 0, bin: 'unsent', fate: 'DROPPED', becomes: 'silence',
      why: 'Nothing leaves. “Don’t air your dirty laundry.”',
    },

    /* ---------- outward channels ---------- */
    friend: {
      kind: 'outward', title: 'Tell a friend the truth', from: 'your gut', receiver: 'one friend',
      k: 1, phi: 1, R0: 0.8, energy: -1, stick: 1, side: 1, up: 0, bin: 'sideways', fate: 'SHARED', becomes: '“me too”',
      why: 'One person hears all of it and might pass it on. Everyone who hears it from a friend keeps carrying it.',
    },
    circle: {
      kind: 'outward', title: 'Speak at a support circle', from: 'a flyer at the library', receiver: '8 people in the same spot',
      k: 8, phi: 1, R0: 0.9, energy: 1, stick: 0.5, side: 1, up: 0, bin: 'sideways', fate: 'SHARED', becomes: 'eight people who recognize it',
      why: 'Speaking costs energy, and being heard gives back more. Half of the people it reaches keep carrying it.',
    },
    groupchat: {
      kind: 'outward', title: 'Start a neighbor group chat', from: 'a neighbor', receiver: '12 neighbors',
      k: 12, phi: 1, R0: 0.7, energy: -1, stick: 0.4, side: 1, up: 0, bin: 'sideways', fate: 'SHARED', becomes: 'a channel that stays open',
      why: 'A standing channel: 40% of everyone it reaches keeps carrying the packet.',
    },
    post: {
      kind: 'outward', title: 'Post about it honestly', from: 'your phone', receiver: 'your followers',
      k: 40, phi: 0.75, R0: 0.6, energy: -1, stick: 0.08, side: 1, up: 0, bin: 'sideways', fate: 'BROADCAST', becomes: 'a public post',
      risk: { p: 0.25, label: 'backlash: “don’t make it weird”', reachMult: 0.5, energy: -1 },
      why: 'Wide but lossy. The feed compresses it (φ = 0.75), few readers carry it, and one post in four draws backlash.',
    },
    paper: {
      kind: 'outward', title: 'Write to the local paper', from: 'an old teacher', receiver: 'readers, and the council',
      k: 60, phi: 0.6, R0: 0.3, energy: -2, stick: 0.05, side: 1, up: 1, bin: 'sideways', fate: 'PRINTED', becomes: 'an edited letter',
      risk: { p: 0.4, label: 'not printed', reachMult: 0 },
      why: 'Editors cut it down (φ = 0.6), and 40% of letters never run. When it does run, the council reads it too.',
    },
    notes: {
      kind: 'outward', title: 'Compare notes', from: 'the people you’ve told', receiver: 'everyone carrying it',
      req: { carriers: 5 }, k: (S) => S.carriers, kText: 'carriers', phi: 1, R0: 1.0, energy: 1, stick: 0.3, side: 1, up: 0,
      flag: 'pattern', bin: 'sideways', fate: 'PATTERN FOUND', becomes: 'a pattern: it isn’t just you',
      why: 'Everyone carrying it compares stories. The particulars cancel and the shared conditions show. Relief gives energy back.',
    },
    name: {
      kind: 'outward', title: 'Name the pattern together', from: 'the circle', receiver: 'everyone who shares it',
      req: { flag: 'pattern' }, k: (S) => S.carriers, kText: 'carriers', phi: 1, R0: 1.2, energy: -2, stick: 0.3, side: 1, up: 0,
      flag: 'named', setFields: 8, lock: true, bin: 'sideways', fate: 'NAMED', becomes: 'a named pattern',
      why: 'A name restores the full message (8/8 fields) and locks it: it can’t be rewritten or dismissed as one person’s issue.',
    },
    aid: {
      kind: 'outward', title: 'Start mutual aid', from: 'the neighbor with the empty fridge', receiver: 'each other',
      req: { carriers: 10 }, k: (S) => S.carriers, kText: 'carriers', phi: 1, R0: 0.8, energy: 2, stick: 0.3, side: 1, up: 1,
      flag: 'aid', bin: 'delivered', fate: 'MET DIRECTLY', becomes: 'met needs, and a list of what’s missing',
      why: 'People meet each other’s needs directly: power held in common. Care flows back, so it restores energy.',
    },
    council: {
      kind: 'outward', title: 'Speak at the council meeting', from: 'a notice on the door', receiver: 'the council, and the room',
      req: { carriers: 10, event: 'council' }, k: (S) => 40 + S.carriers, kText: '40 + carriers', phi: (S) => (S.flags.named ? 1 : 0.6), R0: 0.5,
      energy: -2, stick: 0.15, side: 1, up: 1, bin: 'sideways', fate: 'ON RECORD', becomes: 'public testimony',
      why: 'The council hears it directly. Without a named pattern it lands as one person’s complaint (φ = 0.6).',
    },
    organize: {
      kind: 'outward', title: 'Organize', from: 'everyone who’s heard it', receiver: 'whoever controls the conditions',
      req: { carriers: 30, flag: 'named' }, k: (S) => 2 * S.carriers, kText: '2 × carriers', phi: 1, R0: 1.0, energy: -3, stick: 0.4, side: 1, up: 1,
      flag: 'delivered', bin: 'delivered', fate: 'DELIVERED', becomes: 'one collective demand',
      why: 'A thousand private complaints become one demand, delivered intact. All four tests come back 1.',
    },
  };
  Object.keys(OPTIONS).forEach((id) => { OPTIONS[id].id = id; });

  const STANDARD = ['gym', 'therapy', 'journal', 'meditate', 'hobby', 'selfcare', 'gratitude', 'meds', 'apps', 'selfhelp', 'hr', 'private'];
  const OUTWARD = ['friend', 'circle', 'groupchat', 'post', 'paper', 'notes', 'name', 'aid', 'organize'];

  const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const EVENTS = [
    { text: 'The apartment is quiet most evenings. You realize you haven’t really talked to anyone in weeks.', energy: 0 },
    { text: 'Your manager asks for weekend shifts again. Saying no doesn’t feel like an option.', energy: -1, work: true },
    { text: 'Rent goes up 8%. The notice blames “market conditions.”', energy: -1 },
    { text: 'A coworker admits, quietly, that they’ve been feeling the same way.', carriers: 1, note: '+1 carrier if anyone has heard you' },
    { text: 'Election month. Every channel says the same thing: just vote.', election: true },
    { text: 'The landlord ignores another repair request. The mold is back.', energy: 0 },
    { text: 'A neighbor knocks. Their fridge is empty too.', energy: 0, aid: true },
    { text: 'A heat wave. Everyone is exhausted, and work doesn’t slow down.', energy: -1, work: true },
    { text: 'Someone at work gets written up for complaining.', energy: 0, work: true },
    { text: 'Layoffs are announced. Nobody knows who’s next.', energy: -1 },
    { text: 'The town council schedules a public meeting about rents.', council: true },
    { text: 'The year is ending. One more month to be heard.', energy: 0 },
  ];

  function newState(seed) {
    return {
      seed: seed >>> 0, month: 0, energy: ENERGY_START, reached: 0, carriers: 0, fields: 8, locked: false,
      flags: {}, history: [], offers: [], over: false, eventApplied: -1,
    };
  }

  const val = (x, S) => (typeof x === 'function' ? x(S) : x);

  function requirementText(opt, S) {
    const r = opt.req;
    if (!r) return null;
    const miss = [];
    if (r.carriers && S.carriers < r.carriers) miss.push('needs ' + r.carriers + ' carriers (you have ' + S.carriers + ')');
    if (r.flag === 'pattern' && !S.flags.pattern) miss.push('needs a pattern: compare notes first');
    if (r.flag === 'named' && !S.flags.named) miss.push('needs a named pattern');
    if (r.event && !EVENTS[S.month][r.event]) miss.push('only at the council meeting');
    return miss.length ? miss.join(' · ') : null;
  }

  /* The lens: every number the card shows, computed from the state. */
  function lens(opt, S) {
    const k = Math.max(0, Math.round(val(opt.k, S) || 0));
    const phiC = opt.phi == null ? 1 : val(opt.phi, S);
    const fieldsFrac = S.fields / 8;
    const phi = phiC * fieldsFrac;
    const R = (opt.R0 || 0) * phi;
    let series = 0;
    for (let g = 0; g <= GENERATIONS; g++) series += Math.pow(R, g);
    const E = k * series;
    const remaining = N - S.reached;
    const expNew = remaining * (1 - Math.exp(-E / N));
    const risk = opt.risk || null;
    const rm = risk && risk.reachMult != null ? risk.reachMult : 1;
    const expNewRisk = risk ? expNew * ((1 - risk.p) + risk.p * rm) : expNew;
    const out = k > 0 || opt.out ? 1 : 0;
    // INTACT: a sent packet must arrive with every field; an unsent one only has to stay unrewritten
    const intact = k > 0 ? (phi >= 0.999 ? 1 : 0) : opt.keep && S.fields === 8 ? 1 : 0;
    const gates = [out, intact, opt.side ? 1 : 0, opt.up ? 1 : 0];
    const energyDelta = opt.energy + (risk && risk.energy ? risk.p * risk.energy : 0);
    return {
      k, phiC, phi, fieldsFrac, R, series, E, remaining, expNew, expNewRisk, risk, gates,
      product: gates.every(Boolean) ? 1 : 0, energy: opt.energy, energyExpected: energyDelta,
      stick: opt.stick || 0, expCarriers: expNewRisk * (opt.stick || 0),
    };
  }

  function available(opt, S) {
    const missing = requirementText(opt, S);
    if (missing) return { ok: false, why: missing };
    if (S.energy + opt.energy < 0) return { ok: false, why: 'needs ' + -opt.energy + ' energy (you have ' + S.energy + ')' };
    return { ok: true };
  }

  function pick(arr, r) { return arr[Math.floor(r() * arr.length)]; }
  function shuffle(arr, r) { for (let i = arr.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [arr[i], arr[j]] = [arr[j], arr[i]]; } return arr; }

  /* Start of a month: apply drain and the event, then deal four options. */
  function beginMonth(S) {
    const r = rng(S.seed * 7919 + S.month * 104729 + 17);
    const ev = EVENTS[S.month];
    const notes = [];
    if (S.month > 0) {
      const covered = S.carriers >= COVER_AT;
      const d = covered ? DRAIN - 1 : DRAIN;
      S.energy = Math.max(0, S.energy - d);
      notes.push('work or perish: −' + d + ' energy' + (covered ? ' (your people cover a shift)' : ''));
    }
    if (ev.energy) { S.energy = Math.max(0, S.energy + ev.energy); notes.push((ev.energy > 0 ? '+' : '−') + Math.abs(ev.energy) + ' energy'); }
    if (ev.carriers && S.reached > 0) { S.carriers += ev.carriers; S.reached = Math.min(N, S.reached + ev.carriers); notes.push('+' + ev.carriers + ' carrier'); }
    S.eventNotes = notes;

    // two pieces of standard advice
    const std = STANDARD.slice();
    const offers = [];
    if (ev.election) offers.push('vote');
    if (ev.work && !offers.includes('hr') && r() < 0.7) offers.push('hr');
    while (offers.length < 2) { const id = pick(std, r); if (!offers.includes(id)) offers.push(id); }

    // two outward channels: prefer the next step in the chain, then anything reachable
    const outs = [];
    const want = [];
    if (ev.council) want.push('council');
    if (S.flags.named && !S.flags.delivered) want.push('organize');
    if (S.flags.pattern && !S.flags.named) want.push('name');
    if (S.carriers >= 5 && !S.flags.pattern) want.push('notes');
    if (ev.aid || (S.carriers >= 10 && !S.flags.aid)) want.push('aid');
    for (const id of want) if (outs.length < 2 && !outs.includes(id)) outs.push(id);
    const pool = shuffle(OUTWARD.filter((id) => !outs.includes(id)), r);
    const ready = pool.filter((id) => !requirementText(OPTIONS[id], S));
    const locked = pool.filter((id) => requirementText(OPTIONS[id], S));
    for (const id of ready) if (outs.length < 2) outs.push(id);
    for (const id of locked) if (outs.length < 2) outs.push(id);
    // never deal a dead month: at least one piece of standard advice is always affordable
    if (!offers.some((id) => available(OPTIONS[id], S).ok)) {
      const rest = shuffle(STANDARD.filter((id) => OPTIONS[id].energy >= 0 && !offers.includes(id)), r);
      offers[offers.length - 1] = rest[0];
    }
    S.offers = shuffle(offers.concat(outs), r);
    return S;
  }

  /* Resolve a choice. Returns the receipt and mutates the state. */
  function choose(S, id, rand) {
    const opt = OPTIONS[id];
    const L = lens(opt, S);
    const r = rand || Math.random;
    let mult = 1, riskHit = false;
    if (opt.risk && r() < opt.risk.p) { riskHit = true; mult = opt.risk.reachMult != null ? opt.risk.reachMult : 1; }
    const noise = L.E > 0 ? Math.exp((r() - 0.5) * 0.5) : 1;
    const E = L.E * mult * noise;
    let fresh = Math.round((N - S.reached) * (1 - Math.exp(-E / N)));
    if (L.k > 0 && mult > 0 && fresh === 0 && S.reached < N) fresh = 1;
    fresh = Math.max(0, Math.min(N - S.reached, fresh));
    const carriersGained = Math.round(fresh * (opt.stick || 0));
    const before = { energy: S.energy, reached: S.reached, carriers: S.carriers, fields: S.fields };

    S.reached += fresh;
    S.carriers = Math.min(S.reached, S.carriers + carriersGained);
    let dE = opt.energy + (riskHit && opt.risk.energy ? opt.risk.energy : 0);
    S.energy = Math.max(0, Math.min(ENERGY_MAX, S.energy + dE));
    if (opt.setFields) S.fields = opt.setFields;
    else if (opt.fields && !S.locked) S.fields = Math.max(3, Math.min(8, S.fields + opt.fields));
    else if (opt.fields > 0) S.fields = Math.min(8, S.fields + opt.fields);
    if (opt.lock) S.locked = true;
    if (opt.flag) S.flags[opt.flag] = true;
    if (id === 'vote') S.flags.voted = true;

    const receipt = {
      month: S.month, id, title: opt.title, fate: riskHit && mult === 0 ? 'NOT PRINTED' : opt.fate, bin: opt.bin,
      lens: L, E, noise, riskHit, riskLabel: riskHit ? opt.risk.label : null, fresh, carriersGained,
      before, after: { energy: S.energy, reached: S.reached, carriers: S.carriers, fields: S.fields },
      gates: L.gates, product: riskHit && mult === 0 ? 0 : L.product,
    };
    S.history.push(receipt);
    S.month += 1;
    if (S.month >= MONTHS_TOTAL || S.reached >= N) S.over = true;
    return receipt;
  }

  /* A rough rank for the end screen. */
  function rank(reached) {
    if (reached >= 900) return 'A village';
    if (reached >= 600) return 'A tide';
    if (reached >= 300) return 'A current';
    if (reached >= 100) return 'A ripple';
    if (reached >= 10) return 'A whisper';
    return 'A dead letter';
  }

  const API = { N, MONTHS_TOTAL, ENERGY_MAX, ENERGY_START, DRAIN, COVER_AT, GENERATIONS, OPTIONS, STANDARD, OUTWARD, EVENTS, MONTH_NAMES, rng, newState, beginMonth, choose, lens, available, requirementText, rank };
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
  else root.PacketCore = API;
})(typeof window !== 'undefined' ? window : globalThis);
