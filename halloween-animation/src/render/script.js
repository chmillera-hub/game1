// "The House That Hums" — story, voices and staging.
// Times inside an item: number = seconds from item start (negative = from end),
// '40%' = fraction of the item, 'end', or 'w:word' = when a marked word is spoken.
// Text markers: ^word = hopeful (high note), _word = heavy (low note), ~word = timing only.

const title = 'The House That Hums';

const cast = {
  NAR:     { name: null,             voice: 'bm_george',  speed: 0.90, pitch: 0,    color: '#f3d98e', fx: 'nar' },
  PIP:     { name: 'PIP',            voice: 'af_heart',   speed: 0.93, pitch: 2.5,  color: '#bfe6ff', fx: 'ghost' },
  PATCH:   { name: 'PATCH',          voice: 'am_michael', speed: 0.86, pitch: -3.0, color: '#b4dc8c', fx: 'big' },
  BRAM:    { name: 'AUNTIE BRAMBLE', voice: 'bf_emma',    speed: 0.92, pitch: -0.6, color: '#dcb0ff', fx: 'witch' },
  RATTLE:  { name: 'RATTLE',         voice: 'am_puck',    speed: 1.08, pitch: 1.0,  color: '#ffd27a', fx: 'bones' },
  CLATTER: { name: 'CLATTER',        voice: 'bm_fable',   speed: 1.04, pitch: 0.6,  color: '#ff9fc6', fx: 'bones' },
};

// Which character's mouth moves for each voice
const mouthOf = { PIP: 'pip', PATCH: 'patch', BRAM: 'bram', RATTLE: 'rattle', CLATTER: 'clatter', NAR: 'owl' };

const ridgeY = (x) => 1180 - 0.05 * (x - 540) + 7 * Math.sin(x * 0.013);

const spots = {
  roof: { pip: [470, ridgeY(470)], patch: [775, ridgeY(775)], bramLand: [205, ridgeY(205)], bramKneel: [255, ridgeY(255)] },
  attic: { rattle: [385, 1345], clatter: [700, 1345] },
  hill: { pip: [566, 642], owl: [905, 1112] },
};

const L = (who, text, o = {}) => ({ type: 'line', who, text, ...o });
const B = (dur, o = {}) => ({ type: 'beat', dur, ...o });

const items = [
  // ───────────── 1. HOLLOW HILL ─────────────
  L('NAR', 'Once a year, on the last night of October, the crooked house on Hollow Hill remembers how to ^breathe.', {
    pre: 0.35, post: 0.3, music: 'opening',
    cam: { set: 'hill', at: [540, 960, 1.0], to: [540, 985, 1.07] },
    vars: [
      { at: 'start', titleA: 1, houseGlow: 0.35, windowsLit: 0.25, tr: 0 },
      { at: 'w:breathe', houseGlow: 1, windowsLit: 0.6, breath: 1, tr: 1.6 },
    ],
    acts: [
      { at: 'start', who: 'owl', ex: 'neutral', look: 'cam', tr: 0 },
      { at: 2.2, who: 'owl', look: [540, 1000], tr: 0.6 },
      { at: 'w:breathe', who: 'owl', ex: 'wonder', look: 'cam', tr: 0.5 },
    ],
  }),
  L('NAR', 'Its floorboards ~creak. Its candles ~wake. And everyone who lives inside it... comes ^home.', {
    post: 0.5,
    cam: { to: [560, 1020, 1.28] },
    sfx: [{ at: 'w:creak', name: 'creak' }],
    vars: [
      { at: 0.4, titleA: 0, tr: 1.4 },
      { at: 'w:wake', windowsLit: 1, tr: 1.2 },
      { at: 'w:home', ghostsA: 1, tr: 1.5 },
    ],
    acts: [{ at: 'w:home', who: 'owl', ex: 'warm', tr: 0.5 }],
  }),
  B(1.15, {
    cam: { to: [566, 930, 3.6], ease: 'in' },
    sfx: [{ at: 0.1, name: 'whooshSoft' }],
  }),

  // ───────────── 2. THE ATTIC ─────────────
  L('RATTLE', 'And a one, and a two, and a one, two... ~OW! That\'s my foot!', {
    pre: 0.1, music: 'skeletons',
    cam: { set: 'attic', at: [540, 930, 1.12], to: [540, 960, 1.0], cut: true },
    vars: [{ at: 0, dance: 1, tr: 0 }, { at: 'w:OW', dance: 0, tr: 0.15 }],
    sfx: [{ at: 'w:OW', name: 'clunk' }],
    acts: [
      { at: 0, who: 'rattle', ex: 'joy', pose: 'dance', look: 'clatter', tr: 0 },
      { at: 0, who: 'clatter', ex: 'happy', pose: 'dance', look: 'rattle', tr: 0 },
      { at: 'w:OW', who: 'rattle', ex: 'pain', pose: 'hop', look: 'down', tr: 0.12 },
      { at: 'w:OW', who: 'clatter', ex: 'surprised', pose: 'stand', tr: 0.2 },
      { at: '82%', who: 'rattle', ex: 'indignant', look: 'clatter', tr: 0.3 },
    ],
  }),
  L('CLATTER', 'Technically, it\'s MY foot. You borrowed it in nineteen-oh-four.', {
    post: 0.15,
    cam: { at: [640, 930, 1.35], to: [650, 930, 1.42], cut: true },
    acts: [
      { at: 0, who: 'clatter', ex: 'smug', pose: 'akimbo', look: 'rattle', tr: 0.35 },
      { at: 0, who: 'rattle', pose: 'stand', tr: 0.4 },
      { at: '55%', who: 'clatter', look: 'cam', tr: 0.3 },
      { at: '80%', who: 'clatter', look: 'rattle', tr: 0.3 },
    ],
  }),
  L('RATTLE', 'And you never asked for it ^back!', {
    post: 0.1,
    cam: { at: [430, 930, 1.35], to: [420, 935, 1.42], cut: true },
    acts: [
      { at: 0, who: 'rattle', ex: 'indignant', pose: 'point', look: 'clatter', tr: 0.25 },
      { at: '70%', who: 'rattle', ex: 'laugh', tr: 0.3 },
    ],
  }),
  B(2.2, {
    cam: { at: [540, 960, 1.0], to: [540, 960, 1.04], cut: true },
    sfx: [{ at: 0.2, name: 'bones' }, { at: 1.15, name: 'clunk' }, { at: 1.2, name: 'xyloDown' }],
    vars: [{ at: 0, dance: 0.6, tr: 0.3 }, { at: 1.1, jawDrop: 1, tr: 0.15 }, { at: 1.75, jawDrop: 0, tr: 0.2 }],
    acts: [
      { at: 0, who: 'rattle', ex: 'laugh', pose: 'laugh', look: 'clatter', tr: 0.25 },
      { at: 0, who: 'clatter', ex: 'laugh', pose: 'laugh', look: 'rattle', tr: 0.25 },
      { at: 1.1, who: 'rattle', ex: 'shock', pose: 'catchJaw', look: 'down', tr: 0.15 },
      { at: 1.1, who: 'clatter', ex: 'surprised', pose: 'stand', tr: 0.2 },
      { at: 1.75, who: 'rattle', ex: 'sheepish', look: 'cam', tr: 0.25 },
      { at: 1.8, who: 'clatter', ex: 'amused', look: 'rattle', tr: 0.25 },
    ],
  }),

  // ───────────── 3. THE NEWEST ONE ─────────────
  L('NAR', 'Everyone in the house had a story they could tell. Everyone... _except the _newest one.', {
    pre: 0.15, post: 0.6, music: 'lonely',
    cam: { set: 'hill', at: [566, 905, 2.4], to: [566, 700, 4.6], cut: true, ease: 'inout' },
    vars: [{ at: 0, dance: 0, ghostsA: 0.6, tr: 0 }],
    acts: [{ at: 0, who: 'pip', ex: 'wistful', pose: 'hug', look: 'town', tr: 0 }],
  }),

  // ───────────── 4. THE ROOF ─────────────
  B(1.6, {
    cam: { set: 'roof', at: [540, 960, 1.0], to: [500, 965, 1.22], cut: true },
    sfx: [{ at: 0.2, name: 'wind' }],
    acts: [{ at: 0, who: 'pip', ex: 'wistful', pose: 'hug', look: 'town', tr: 0 }, { at: 0, who: 'patch', vis: 0, tr: 0 }, { at: 0, who: 'bram', vis: 0, tr: 0 }],
  }),
  L('PIP', 'The skeletons were dancers. Auntie Bramble kept a lighthouse. Patch was... a whole lot of people.', {
    post: 0.4,
    cam: { to: [470, 990, 1.75] },
    acts: [
      { at: 0, who: 'pip', ex: 'wistful', look: 'town', tr: 0.5 },
      { at: '62%', who: 'pip', ex: 'amused', look: [520, 1100], pose: 'sit', tr: 0.4 },
      { at: '92%', who: 'pip', ex: 'wistful', tr: 0.8 },
    ],
  }),
  L('PIP', 'And me? I just woke up in a sheet.', {
    post: 0.55,
    cam: { to: [470, 985, 2.0] },
    acts: [
      { at: 0, who: 'pip', ex: 'shy', look: 'cam', tr: 0.4 },
      { at: '45%', who: 'pip', ex: 'sad', look: 'down', pose: 'handsLap', tr: 0.6 },
    ],
  }),
  L('PIP', 'I don\'t even _know my real name. Pip is just the sound I made when I got here.', {
    post: 0.5, speed: 0.88,
    cam: { to: [470, 975, 2.3] },
    vars: [{ at: 'end', sigh: 1, tr: 0.6 }],
    acts: [
      { at: 0, who: 'pip', ex: 'sad', look: 'down', tr: 0.4 },
      { at: '55%', who: 'pip', ex: 'verysad', look: 'town', pose: 'hug', tr: 0.7 },
    ],
  }),
  B(1.7, {
    music: 'tiptoe',
    cam: { to: [610, 900, 1.15], ease: 'inout' },
    sfx: [{ at: 0.0, name: 'creak' }, { at: 0.7, name: 'creak2' }, { at: 1.25, name: 'thump' }],
    vars: [{ at: 0, sigh: 0, tr: 0.5 }],
    acts: [
      { at: 0.05, who: 'pip', ex: 'surprised', look: [790, 1100], tr: 0.18 },
      { at: 0.0, who: 'patch', vis: 1, pose: 'climb', climb: 0, sitDown: 0, ex: 'effort', look: 'pip', tr: 0 },
      { at: 0.15, who: 'patch', climb: 0.55, tr: 0.6 },
      { at: 0.8, who: 'patch', climb: 1, tr: 0.55 },
      { at: 0.75, who: 'pip', look: 'patch', tr: 0.25 },
      { at: 1.35, who: 'patch', ex: 'warm', pose: 'holdPumpkin', tr: 0.35 },
      { at: 1.4, who: 'pip', ex: 'curious', tr: 0.4 },
    ],
  }),
  L('PATCH', 'Mind if I sit?', {
    post: 0.2,
    cam: { at: [690, 820, 1.55], to: [690, 830, 1.6], cut: true },
    acts: [{ at: 0, who: 'patch', ex: 'sheepish', look: 'pip', tr: 0.3 }],
  }),
  B(1.3, {
    cam: { at: [620, 910, 1.2], cut: true },
    sfx: [{ at: 0.15, name: 'creakBig' }],
    vars: [{ at: 0.15, roofShake: 1, tr: 0.05 }, { at: 0.5, roofShake: 0, tr: 0.6 }],
    acts: [
      { at: 0.1, who: 'patch', sitDown: 1, tr: 0.25 },
      { at: 0.2, who: 'patch', ex: 'frozen', look: 'down', tr: 0.15 },
      { at: 0.2, who: 'pip', ex: 'shock', tr: 0.15 },
      { at: 0.9, who: 'pip', ex: 'amused', tr: 0.3 },
    ],
  }),
  L('PATCH', '...The roof minds. I\'ll sit ~gently.', {
    post: 0.1,
    acts: [
      { at: 0, who: 'patch', ex: 'sheepish', look: [700, 1250], tr: 0.3 },
      { at: 'w:gently', who: 'patch', sitDown: 0.6, ex: 'sheepish', look: 'pip', tr: 0.9 },
    ],
  }),
  B(1.5, {
    sfx: [{ at: 0.1, name: 'giggle' }],
    acts: [
      { at: 0, who: 'pip', ex: 'giggle', pose: 'mouthCover', tr: 0.2 },
      { at: 0.2, who: 'patch', ex: 'happy', tr: 0.4 },
      { at: 0.3, who: 'patch', sitDown: 1, tr: 1.4 },
      { at: 1.2, who: 'pip', pose: 'sit', ex: 'happy', tr: 0.4 },
    ],
  }),
  L('PIP', 'Patch... do you remember? Who you were... before?', {
    post: 0.3, speed: 0.9, music: 'patch',
    cam: { at: [560, 960, 1.65], to: [555, 955, 1.8], cut: true },
    acts: [
      { at: 0, who: 'pip', ex: 'worried', look: 'patch', tr: 0.5 },
      { at: '50%', who: 'patch', ex: 'thoughtful', tr: 0.6 },
    ],
  }),
  B(1.6, {
    cam: { at: [765, 760, 1.7], to: [765, 770, 1.95], cut: true },
    acts: [
      { at: 0.1, who: 'patch', ex: 'thoughtful', look: 'hands', pose: 'lookHands', tr: 0.9 },
    ],
  }),
  L('PATCH', 'Which one?', {
    post: 0.5,
    acts: [{ at: 0, who: 'patch', ex: 'wry', look: 'hands', tr: 0.4 }],
  }),
  L('PATCH', 'These hands belonged to a clockmaker. I can still feel them wanting to fix things.', {
    post: 0.35,
    vars: [{ at: '45%', fingers: 1, tr: 0.3 }, { at: '95%', fingers: 0, tr: 0.4 }],
    acts: [{ at: '50%', who: 'patch', ex: 'fond', tr: 0.5 }],
  }),
  L('PATCH', 'This ear was a fisherman\'s. It hears the ^sea every time it rains.', {
    post: 0.4,
    cam: { to: [770, 740, 2.05] },
    acts: [
      { at: 0, who: 'patch', pose: 'touchEar', look: 'up', ex: 'fond', tr: 0.5 },
      { at: 'w:sea', who: 'patch', ex: 'dreamy', tr: 0.6 },
    ],
  }),
  L('PATCH', 'And this heart...', {
    post: 0.7, speed: 0.82,
    acts: [{ at: 0, who: 'patch', pose: 'handChest', ex: 'vulnerable', look: 'down', tr: 0.7 }],
  }),
  L('PATCH', 'I _never found out whose heart this is.', {
    post: 0.6, speed: 0.82,
    cam: { to: [770, 735, 2.2] },
    acts: [{ at: '60%', who: 'patch', ex: 'sadsmile', tr: 0.8 }],
  }),
  L('PIP', 'Doesn\'t that scare you?', {
    post: 0.45, speed: 0.86,
    cam: { at: [470, 975, 2.15], to: [470, 975, 2.25], cut: true },
    acts: [{ at: 0, who: 'pip', ex: 'worried', look: 'patch', pose: 'hug', tr: 0.4 }],
  }),
  L('PATCH', 'It used to. I thought if I was made of everybody else... then I must be _nobody.', {
    post: 0.7,
    cam: { at: [690, 790, 1.55], to: [700, 780, 1.7], cut: true },
    acts: [
      { at: 0, who: 'patch', ex: 'distant', look: 'town', pose: 'holdPumpkin', tr: 0.7 },
      { at: 'w:nobody', who: 'patch', ex: 'verysad', tr: 0.6 },
      { at: '30%', who: 'pip', ex: 'sad', look: 'patch', tr: 0.5 },
    ],
  }),
  L('PIP', 'What ^changed?', {
    post: 0.5,
    cam: { at: [560, 940, 1.55], to: [560, 935, 1.6], cut: true },
    acts: [{ at: 0, who: 'pip', ex: 'hopeful', look: 'patch', pose: 'sit', tr: 0.4 }],
  }),
  B(0.9, {
    acts: [{ at: 0.1, who: 'patch', ex: 'warm', look: 'pip', tr: 0.6 }],
  }),
  L('PATCH', 'Somebody asked me what face I wanted to carve.', {
    post: 0.4,
    cam: { at: [700, 800, 1.6], to: [705, 790, 1.7], cut: true },
    acts: [{ at: 0, who: 'patch', ex: 'warm', look: 'pip', tr: 0.4 }, { at: '60%', who: 'patch', look: 'pumpkin', tr: 0.4 }],
  }),
  L('PATCH', 'Not the clockmaker\'s face. Not the fisherman\'s. ^Mine.', {
    post: 0.9, music: 'warm',
    cam: { to: [660, 880, 1.35] },
    vars: [{ at: '35%', patchTurn: 1, tr: 1.4 }],
    sfx: [{ at: 'w:Mine', name: 'glowChime' }],
    acts: [
      { at: 0, who: 'patch', ex: 'proud', look: 'pip', tr: 0.4 },
      { at: '35%', who: 'patch', pose: 'showPumpkin', tr: 1.2 },
      { at: 'w:Mine', who: 'pip', ex: 'wonder', look: 'patchPumpkin', tr: 0.5 },
      { at: 'w:Mine', who: 'patch', ex: 'beam', tr: 0.4 },
    ],
  }),

  // ───────────── 5. AUNTIE BRAMBLE ─────────────
  B(1.9, {
    cam: { at: [540, 900, 1.0], to: [480, 930, 1.12], cut: true, ease: 'out' },
    sfx: [{ at: 0.0, name: 'whoosh' }, { at: 1.05, name: 'whoosh2' }, { at: 1.6, name: 'thump' }],
    vars: [{ at: 0, bramFly: 0, tr: 0 }, { at: 0, bramFly: 1, tr: 1.65, ease: 'inout' }],
    acts: [
      { at: 0, who: 'bram', vis: 1, pose: 'fly', ex: 'joy', look: 'pip', tr: 0 },
      { at: 0.1, who: 'pip', ex: 'surprised', look: 'bram', tr: 0.2 },
      { at: 0.1, who: 'patch', ex: 'amused', look: 'bram', pose: 'holdPumpkin', tr: 0.4 },
      { at: 1.65, who: 'bram', pose: 'stand', ex: 'happy', tr: 0.25 },
    ],
  }),
  L('BRAM', 'Is this a private brood, or can an old witch join in?', {
    post: 0.3, music: 'witch',
    cam: { at: [250, 820, 1.5], to: [258, 826, 1.58], cut: true },
    acts: [{ at: 0, who: 'bram', ex: 'playful', look: 'pip', tr: 0.3 }],
  }),
  B(0.9, {
    cam: { at: [380, 930, 1.45], cut: true },
    acts: [
      { at: 0.0, who: 'pip', ex: 'sad', look: 'down', pose: 'hug', tr: 0.6 },
      { at: 0.45, who: 'bram', ex: 'concerned', look: 'pip', tr: 0.5 },
    ],
  }),
  L('PIP', 'Auntie... I don\'t remember anything. Not one thing.', {
    post: 0.4, speed: 0.88, music: 'tender',
    cam: { at: [470, 975, 2.2], to: [470, 975, 2.35], cut: true },
    acts: [{ at: 0, who: 'pip', ex: 'verysad', look: 'down', tr: 0.4 }, { at: '50%', who: 'pip', look: 'bram', tr: 0.4 }],
  }),
  L('PIP', 'What if there\'s _nothing inside me at all?', {
    post: 0.6, speed: 0.84,
    cam: { to: [470, 970, 2.5] },
    acts: [{ at: 0, who: 'pip', ex: 'teary', look: 'bram', tr: 0.5 }],
  }),
  B(1.4, {
    cam: { at: [330, 925, 1.5], to: [335, 932, 1.6], cut: true },
    acts: [
      { at: 0, who: 'bram', ex: 'tender', pose: 'kneel', tr: 1.0 },
      { at: 0.0, who: 'bram', x: 200, tr: 1.0 },
      { at: 0.9, who: 'bram', blink: 1 },
    ],
  }),
  L('BRAM', 'Oh, little light. Memory isn\'t a trunk in the attic that you lose the key to.', {
    post: 0.35, speed: 0.88,
    cam: { at: [215, 890, 1.95], to: [218, 886, 2.05], cut: true },
    acts: [{ at: 0, who: 'bram', ex: 'tender', look: 'pip', tr: 0.4 }, { at: '50%', who: 'bram', ex: 'gentle', tr: 0.4 }],
  }),
  L('BRAM', 'It\'s more like a ^lantern. You don\'t carry it behind you.', {
    post: 0.4, speed: 0.88,
    vars: [{ at: '30%', bramPumpkin: 1, tr: 0.6 }],
    sfx: [{ at: '30%', name: 'sparkle' }],
    acts: [{ at: '28%', who: 'bram', pose: 'offer', ex: 'warm', tr: 0.6 }],
  }),
  L('BRAM', 'You carry it ^ahead.', {
    post: 0.6, speed: 0.86,
    cam: { at: [370, 950, 1.55], to: [380, 955, 1.62], cut: true },
    vars: [{ at: '70%', pumpkinToPip: 1, tr: 0.7 }],
    acts: [
      { at: 0, who: 'bram', ex: 'warm', tr: 0.3 },
      { at: 0.1, who: 'pip', ex: 'curious', look: 'pipPumpkin', tr: 0.5 },
      { at: '70%', who: 'pip', pose: 'holdPumpkin', tr: 0.6 },
      { at: '85%', who: 'bram', pose: 'kneel', tr: 0.6 },
    ],
  }),
  L('PIP', 'But... I don\'t know what face to carve.', {
    post: 0.5, speed: 0.9,
    cam: { at: [470, 980, 2.0], to: [470, 980, 2.1], cut: true },
    acts: [{ at: 0, who: 'pip', ex: 'worried', look: 'pipPumpkin', tr: 0.4 }, { at: '60%', who: 'pip', look: 'patch', tr: 0.4 }],
  }),
  L('PATCH', 'Then don\'t carve the face you were.', {
    post: 0.45,
    cam: { at: [700, 800, 1.65], to: [690, 810, 1.75], cut: true },
    acts: [{ at: 0, who: 'patch', ex: 'encouraging', look: 'pip', pose: 'lean', tr: 0.5 }],
  }),
  L('PATCH', 'Carve the one you\'re ^going to be.', {
    post: 0.5,
    acts: [{ at: 0, who: 'patch', ex: 'warm', tr: 0.4 }],
  }),

  // ───────────── 6. CARVING ─────────────
  B(5.6, {
    music: 'carving',
    cam: { at: [470, 1010, 2.1], to: [470, 1000, 2.2], cut: true },
    sfx: [{ at: 0.3, name: 'carve' }, { at: 1.3, name: 'carve' }, { at: 2.0, name: 'carve' }, { at: 4.4, name: 'carve' }],
    vars: [{ at: 0.2, carving: 1, tr: 0.2 }, { at: 0.2, carve: 1, tr: 5.0, ease: 'linear' }, { at: 5.3, carving: 0, tr: 0.2 }],
    acts: [
      { at: 0, who: 'pip', ex: 'concentrate', pose: 'carve', look: 'pipPumpkin', tr: 0.4 },
      { at: 2.6, who: 'patch', ex: 'warm', look: 'bram', tr: 0.4 },
      { at: 2.75, who: 'bram', ex: 'warm', look: 'patch', tr: 0.4 },
      { at: 3.5, who: 'patch', ex: 'knowing', tr: 0.3 },
      { at: 3.6, who: 'bram', ex: 'knowing', tr: 0.3 },
      { at: 4.3, who: 'patch', look: 'pip', tr: 0.4 },
      { at: 4.4, who: 'bram', look: 'pip', tr: 0.4 },
    ],
    camKeys: [
      { at: 2.45, pos: [560, 930, 1.25], cut: true },
      { at: 4.2, pos: [555, 925, 1.3] },
      { at: 4.25, pos: [470, 1010, 2.15], cut: true },
    ],
  }),
  B(1.3, {
    cam: { at: [430, 960, 1.6], to: [440, 960, 1.7], cut: true },
    vars: [{ at: 0.1, pipTurn: 1, tr: 1.0 }],
    acts: [{ at: 0.0, who: 'pip', ex: 'shy', pose: 'present', look: 'bram', tr: 0.5 }],
  }),
  L('PIP', 'It\'s... crooked.', {
    post: 0.4, speed: 0.9,
    acts: [{ at: 0, who: 'pip', ex: 'shy', look: 'patch', tr: 0.4 }],
  }),
  L('PATCH', 'So am ^I.', {
    post: 0.35,
    cam: { at: [700, 800, 1.6], cut: true },
    acts: [{ at: 0, who: 'patch', ex: 'grin', pose: 'pointSelf', look: 'pip', tr: 0.35 }],
  }),
  L('BRAM', 'Crooked is how the ^light gets out.', {
    post: 0.2, speed: 0.9,
    cam: { at: [330, 900, 1.6], to: [340, 905, 1.65], cut: true },
    vars: [{ at: 'end', spark: 1, tr: 0.05 }],
    acts: [{ at: 0, who: 'bram', ex: 'knowing', pose: 'snap', look: 'pipPumpkin', tr: 0.4 }],
  }),
  B(2.3, {
    music: 'wonder',
    cam: { at: [470, 985, 2.0], to: [470, 975, 2.45], cut: true },
    sfx: [{ at: 0.0, name: 'snap' }, { at: 0.05, name: 'ignite' }],
    vars: [{ at: 0.0, spark: 0, tr: 0.5 }, { at: 0.05, pipLit: 1, tr: 0.7 }],
    acts: [
      { at: 0.1, who: 'pip', ex: 'wonder', look: 'pipPumpkin', pose: 'holdPumpkin', tr: 0.8 },
      { at: 1.4, who: 'pip', look: 'far', tr: 0.8 },
      { at: 0.2, who: 'bram', pose: 'kneel', tr: 0.5 },
    ],
  }),
  L('PIP', 'Oh... I remember something.', {
    post: 0.55, speed: 0.84,
    acts: [{ at: 0, who: 'pip', ex: 'wonder', look: 'far', tr: 0.4 }],
  }),
  L('PIP', 'Someone used to hum. In a ^warm kitchen, while the bread was rising.', {
    post: 0.45, speed: 0.88,
    cam: { to: [470, 970, 2.6] },
    acts: [{ at: 0, who: 'pip', ex: 'remember', tr: 0.6 }],
  }),
  L('PIP', 'It went... _low... and then ^high... and then ^home.', {
    post: 0.8, speed: 0.86,
    cam: { at: [450, 960, 1.55], to: [450, 960, 1.6], cut: true },
    motif: true,
    acts: [
      { at: 'w:low', who: 'pip', pose: 'gestLow', ex: 'remember', tr: 0.4 },
      { at: 'w:high', who: 'pip', pose: 'gestHigh', ex: 'joy', tr: 0.4 },
      { at: 'w:home', who: 'pip', pose: 'holdPumpkin', ex: 'content', tr: 0.6 },
      { at: 0.4, who: 'bram', ex: 'moved', look: 'pip', tr: 0.6 },
      { at: 0.4, who: 'patch', ex: 'moved', look: 'pip', tr: 0.6 },
    ],
  }),
  B(1.5, {
    cam: { at: [215, 890, 2.0], to: [215, 890, 2.1], cut: true },
    acts: [
      { at: 0.1, who: 'bram', ex: 'teary', pose: 'handMouth', look: 'down', tr: 0.6 },
      { at: 1.0, who: 'bram', look: 'pip', tr: 0.4 },
    ],
  }),
  L('BRAM', 'That\'s not nothing, little light. That\'s a whole ^kitchen.', {
    post: 0.5, speed: 0.86,
    acts: [{ at: 0, who: 'bram', ex: 'teary', pose: 'kneel', look: 'pip', tr: 0.5 }, { at: '50%', who: 'bram', ex: 'tearsmile', tr: 0.5 }],
  }),
  L('PIP', 'It\'s not my name. It\'s not where I lived. It\'s just... ^warm.', {
    post: 0.45, speed: 0.88,
    cam: { at: [470, 975, 2.2], to: [470, 975, 2.3], cut: true },
    acts: [{ at: 0, who: 'pip', ex: 'thoughtful', look: 'pipPumpkin', tr: 0.5 }, { at: 'w:warm', who: 'pip', ex: 'content', look: 'bram', tr: 0.6 }],
  }),
  L('PATCH', 'Warm is a good place to ^start.', {
    post: 0.6,
    cam: { at: [700, 800, 1.6], to: [700, 800, 1.65], cut: true },
    acts: [{ at: 0, who: 'patch', ex: 'warm', look: 'pip', pose: 'holdPumpkin', tr: 0.5 }],
  }),

  // ───────────── 7. THE HOUSE HUMS ─────────────
  B(6.0, {
    music: 'hum',
    cam: { at: [470, 975, 2.0], to: [520, 930, 1.05], cut: true, ease: 'inout' },
    vars: [{ at: 0, hum: 1, tr: 0.6 }],
    acts: [
      { at: 0, who: 'pip', ex: 'humming', look: 'far', pose: 'holdPumpkin', tr: 0.6 },
      { at: 2.0, who: 'patch', ex: 'content', tr: 0.6 },
      { at: 2.3, who: 'bram', ex: 'content', tr: 0.6 },
    ],
  }),
  L('RATTLE', 'Hey! Who taught the house a new ^song?', {
    pre: 0.0, post: 0.15,
    cam: { set: 'attic', at: [540, 930, 1.12], to: [540, 940, 1.18], cut: true },
    vars: [{ at: 0, dance: 0, jawDrop: 0, tr: 0 }],
    acts: [
      { at: 0, who: 'rattle', ex: 'joy', pose: 'fiddle', look: 'up', tr: 0 },
      { at: 0, who: 'clatter', ex: 'wonder', pose: 'lookUp', look: 'up', tr: 0 },
      { at: '70%', who: 'rattle', look: 'clatter', tr: 0.3 },
    ],
  }),
  L('CLATTER', 'Shh! You\'ll make it ~shy.', {
    post: 0.5, speed: 0.95,
    acts: [
      { at: 0, who: 'clatter', ex: 'shush', pose: 'shush', look: 'rattle', tr: 0.25 },
      { at: '80%', who: 'clatter', ex: 'tender', pose: 'lookUp', look: 'up', tr: 0.6 },
      { at: '85%', who: 'rattle', ex: 'content', look: 'up', tr: 0.6 },
    ],
  }),
  B(5.6, {
    cam: { set: 'hill', at: [560, 1000, 1.3], to: [545, 965, 1.02], cut: true, ease: 'out' },
    vars: [
      { at: 0, windowsLit: 0.5, ghostsA: 1, houseGlow: 1, tr: 0 },
      { at: 0.2, windowsLit: 1.2, tr: 3.5 },
      { at: 0.3, ghostsUp: 1, tr: 5.0, ease: 'linear' },
      { at: 0, pipLit: 1, hum: 1, tr: 0 },
    ],
    acts: [{ at: 0, who: 'pip', ex: 'humming', pose: 'holdPumpkin', look: 'far', tr: 0 }, { at: 2.5, who: 'owl', ex: 'warm', look: [566, 640], tr: 0.6 }],
  }),

  // ───────────── 8. A NAME ─────────────
  L('PIP', 'Auntie? Can I keep the name... ^Pip?', {
    pre: 0.2, post: 0.35, speed: 0.88, music: 'ending',
    cam: { set: 'roof', at: [440, 930, 1.3], to: [420, 950, 1.5], cut: true },
    vars: [{ at: 0, hum: 0, ghostsUp: 0, tr: 0 }],
    acts: [
      { at: 0, who: 'pip', ex: 'sleepy', pose: 'holdPumpkin', look: 'bram', tr: 0 },
      { at: 0, who: 'bram', ex: 'content', pose: 'armAround', look: 'pip', tr: 0 },
      { at: 0, who: 'patch', ex: 'content', pose: 'holdPumpkin', look: 'pip', tr: 0 },
      { at: 0, who: 'pip', x: 400, tr: 0 },
    ],
  }),
  L('BRAM', 'It\'s yours, little light. You ^made it.', {
    post: 0.8, speed: 0.86,
    cam: { to: [340, 935, 1.7] },
    acts: [
      { at: 0, who: 'bram', ex: 'tender', tr: 0.4 },
      { at: '75%', who: 'pip', ex: 'content', look: 'cam', tr: 0.5 },
      { at: '85%', who: 'pip', blink: 1 },
    ],
  }),

  // ───────────── 9. WHAT WE CHOOSE ─────────────
  L('NAR', 'Pip never did find the old name. But that night, Pip found something we all forget... and have to find ^again.', {
    post: 0.5,
    cam: { to: [540, 900, 1.0], ease: 'inout' },
    acts: [{ at: '40%', who: 'pip', ex: 'sleepy', look: 'town', tr: 0.8 }],
  }),
  L('NAR', 'We are not only made of what we\'ve _lost.', {
    post: 0.65, speed: 0.86, music: 'finale',
    cam: { set: 'hill', at: [566, 720, 3.6], to: [560, 900, 1.9], cut: true, ease: 'inout' },
    vars: [{ at: 0, windowsLit: 1, ghostsA: 1, pipLit: 1, ghostsUp: 0, tr: 0 }],
    acts: [{ at: 0, who: 'pip', ex: 'content', pose: 'holdPumpkin', look: 'town', tr: 0 }],
  }),
  L('NAR', 'We are made of what we choose to ^light.', {
    post: 3.4, speed: 0.86,
    cam: { to: [540, 960, 1.0], ease: 'out' },
    vars: [{ at: 'w:light', titleA: 1, endGlow: 1, tr: 2.0 }],
    sfx: [{ at: -1.6, name: 'hoot' }],
    acts: [{ at: -1.7, who: 'owl', ex: 'warm', look: 'cam', tr: 0.4 }, { at: -0.6, who: 'owl', blink: 1 }],
  }),
];

module.exports = { title, cast, items, spots, mouthOf, ridgeY };
