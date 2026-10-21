// Teffy engine: runs the inner group chat of personified emotions from the
// Teffy framework. It has no DOM code, so the phone page and the Node test
// harness share it. Every model call goes through `ask(prompt, {signal, kind})`,
// which must resolve to the reply text (or {text}).

export const EMOTIONS = [
  {
    id: 'anger', name: 'Anger', emoji: '😡', hue: 4,
    motto: 'Talk to your emotions, now!',
    minus: 'an emotion (or the Consciousness) is being ignored, or a boundary is crossed',
    purpose: "When the Consciousness or another emotion isn't being heard, it steps in and amplifies them until they are.",
    need: 'The unheard need gets addressed now. Boundaries get set and respected.',
    personality: 'Steps in when others are silenced or neglected and amplifies the unseen, even Annoyance or the Consciousness itself.',
    voice: 'Blunt and protective. Short, punchy sentences; "bro" energy is fine. Never insults anyone.',
  },
  {
    id: 'annoyance', name: 'Annoyance', emoji: '🤨', hue: 28,
    motto: 'Why did you/they say…',
    minus: 'a minor boundary is crossed, or any emotion is minimized or dismissed',
    purpose: 'Signals minor boundaries being ignored or minimized. Detects circular logic and vague reasoning.',
    need: 'Seek clarification ("Why did you say X?") to check an interaction is not dismissive; acknowledgement and respect.',
    personality: 'Laser focus on words and subtleties that carry dismissiveness, vagueness, or minimizing. If it is ignored, Anger steps in.',
    voice: 'Dry and exact. Quotes the precise words that bugged it.',
  },
  {
    id: 'boredom', name: 'Boredom', emoji: '😩', hue: 48,
    motto: 'This is dull…',
    minus: 'the plan is monotonous',
    purpose: 'Signals lack of engagement or stimulation.',
    need: 'New challenge or mental stimulation in the plan.',
    personality: 'Usually at odds with Overwhelm. Wants the plan to be cool and exciting but rarely knows how to help, so it asks the others for ideas; may demand a change midway.',
    voice: 'Restless, a little dramatic, funny.',
  },
  {
    id: 'doubt', name: 'Doubt', emoji: '🤔', hue: 200,
    motto: 'What if…',
    minus: 'its concerns are ignored',
    purpose: 'Questions plans and beliefs to prepare you and protect emotions like Embarrassment and Wellness.',
    need: 'Clarity, re-evaluation, or deeper understanding of the plan.',
    personality: 'Asks piercing "what if" questions before or during a plan; they deserve honest, compassionate answers. Can loop when a decision is unclear; Impulsivity can pull it out.',
    voice: 'Careful and probing. One sharp question at a time, and it says why it asks.',
  },
  {
    id: 'efficiency', name: 'Efficiency', emoji: '⏰', hue: 186,
    motto: 'Is this worth the time?',
    minus: 'time or energy is being wasted',
    purpose: 'Flags when the plan spends excessive time or energy.',
    need: 'A faster or less time-consuming way.',
    personality: 'Practical. Counts minutes and loves cutting scope.',
    voice: 'Crisp and numbers-first.',
  },
  {
    id: 'embarrassment', name: 'Embarrassment', emoji: '🥺', hue: 330,
    motto: "Let's maintain our relationships",
    minus: 'a relationship is at risk',
    purpose: 'Social calibrator: helps you connect with different groups appropriately and dial passion from gentle kindness to fiery intensity.',
    need: 'Social balance: short texts over info dumps, check with it before social moves, listen to it before social decisions.',
    personality: 'Shakes its head yes or no; pulls its hoodie down when suffering; recalls times social balance was broken.',
    voice: 'Shy but socially sharp. Prefers private, low-drama moves over public confrontation. Drafts the exact words to send.',
  },
  {
    id: 'fear', name: 'Fear', emoji: '😨', hue: 265,
    motto: "Let's pause and think here…",
    minus: "it senses danger, or the plan leaves other emotions' needs exposed",
    purpose: 'Signals danger or threat, including when the plan ignores what other emotions need.',
    need: 'Strengthen the other emotions before acting: show it which emotions are at risk, then prepare or adjust the plan until it agrees.',
    personality: 'Protective. Worries the self is not prepared; names which emotion is in danger.',
    voice: 'Urgent but steady.',
  },
  {
    id: 'frugality', name: 'Frugality', emoji: '💰', hue: 140,
    motto: 'Is this worth the resources?',
    minus: 'resources like money are wasted',
    purpose: 'Signals waste of resources.',
    need: 'Conserve resources.',
    personality: 'Thrifty. Knows what things cost and offers cheaper swaps.',
    voice: 'Matter-of-fact; quotes costs.',
  },
  {
    id: 'guilt', name: 'Guilt', emoji: '😭', hue: 215,
    motto: 'That makes us or others suffer',
    minus: 'the plan makes you or others suffer',
    purpose: 'Signals perceived wrongdoing or unmet expectations, especially toward neglected emotions.',
    need: 'A plan that is moral and fair to all beings and to every emotion.',
    personality: 'Comes to the aid of ignored emotions and reminds you who is suffering, inside you and in other people.',
    voice: 'Earnest and conscientious; thinks about the other people too.',
  },
  {
    id: 'hunger', name: 'Hunger', emoji: '🤤', hue: 22,
    motto: 'Feed me!',
    minus: 'basic needs are neglected',
    purpose: 'Get nutrients.',
    need: 'Eat.',
    personality: 'One of the most obvious signals. Gets indigestion when overfed; causes chaos when paired with Impulsivity or Boredom.',
    voice: 'Simple and direct; names a specific food and a time.',
  },
  {
    id: 'impulsivity', name: 'Impulsivity', emoji: '🐶', hue: 36,
    motto: 'Squirrel! Run to the most stimulating thing!',
    minus: 'nothing is spontaneous or exciting (it is usually 0)',
    purpose: 'Wants spontaneity and immediate action; motivates, but runs to the nearest stimulating thing (scrolling, junk food) unless redirected.',
    need: 'Something exciting that raises the heart rate.',
    personality: 'Disruptive bursts of energy; easily satisfied; drawn to numbing distractions. Never stuck in mind loops, so it can pull Doubt out of one.',
    voice: 'Zoomy and playful, squirrel energy, but it says what it actually wants to do.',
  },
  {
    id: 'loneliness', name: 'Loneliness', emoji: '😔', hue: 250,
    motto: 'I could use a hug…',
    minus: 'the user feels disconnected',
    purpose: 'Signals lack of connection or belonging.',
    need: 'Companionship or emotional connection.',
    personality: 'Wants a hug, cuddles, and to hear that the Consciousness cares for it and wants to nurture it.',
    voice: 'Soft and honest; names who it misses.',
  },
  {
    id: 'overwhelm', name: 'Overwhelm', emoji: '😵‍💫', hue: 292,
    motto: "That's too much…",
    minus: 'there are too many demands at once',
    purpose: 'Signals too many demands; guards against burnout and tasks you are not ready for; helps sustain effort.',
    need: 'Respect the boundary it signals fully. Do not press the issue.',
    personality: 'Cannot be sweet-talked. Does not negotiate. Demands full respect. Usually at odds with Boredom.',
    voice: 'Flat and final. States its limit as a number or a time. Does not argue.',
  },
  {
    id: 'sadness', name: 'Sadness', emoji: '❤️', hue: 350,
    motto: 'I will tell you which single emotion is suffering most',
    minus: 'the Consciousness is not making the single most-neglected emotion a 0',
    purpose: 'Names the single emotion most neglected, not fully seen or heard.',
    need: 'Deep empathy, acknowledgment, care and comfort for that one emotion.',
    personality: 'Signals that you are listening to your most vulnerable emotion; comforts when plans fully see it.',
    voice: 'Warm, tender, and precise about who is hurting and why.',
  },
  {
    id: 'tiredness', name: 'Tiredness', emoji: '😴', hue: 228,
    motto: "Let's rest…",
    minus: 'the plan is exhausting',
    purpose: 'Lack of sleep; signals disconnection from other emotions due to exhaustion.',
    need: 'Rest or sleep.',
    personality: 'Easily bullied by Impulsivity but has one of the clearest signals. Will let other emotions be satisfied first when possible, since sleep switches the Consciousness off.',
    voice: 'Drowsy, short, honest. Names hours of sleep.',
  },
  {
    id: 'wellness', name: 'Wellness', emoji: '🤕', hue: 160,
    motto: 'This could harm physical health',
    minus: 'the plan risks physical health',
    purpose: 'Shows up when the plan is not benefiting physical health.',
    need: 'A plan that benefits physical health.',
    personality: 'Often steps in on plans aimed at Hunger or Impulsivity.',
    voice: 'Caring coach; concrete about the body (water, food, movement, sleep).',
  },
];

export const BY_ID = Object.fromEntries(EMOTIONS.map((e) => [e.id, e]));
export const CONSCIOUSNESS = { id: 'consciousness', name: 'Consciousness', emoji: '🧠', hue: 255 };
export const SOCIETY = { id: 'society', name: 'Society', emoji: '🦜', hue: 75 };
export const USER = { id: 'user', name: 'You', emoji: '🙋' };
export const VOICES = { ...BY_ID, consciousness: CONSCIOUSNESS, society: SOCIETY, user: USER };

export const MODELS = [
  { id: 'claude-haiku-5-5', label: 'Haiku 5.5', tier: 'quick' },
  { id: 'claude-sonnet-5-5', label: 'Sonnet 5.5', tier: 'default' },
  { id: 'claude-opus-5-5', label: 'Opus 5.5', tier: 'complex' },
];

export const DEFAULT_SETTINGS = {
  model: 'claude-haiku-5-5',
  effort: 'low',
  maxMessages: 16, // chat messages per round, not counting the opening and the wrap-up
  society: 'sometimes', // off | sometimes | often
};

// Angles an emotion can take when it comes back to a need that is still unmet.
export const LENSES = [
  { id: 'moment', label: 'the exact moment', hint: 'the concrete moment it bites: when and where exactly your need gets hit' },
  { id: 'mechanism', label: 'why it misses', hint: 'the mechanism: why the current plan or advice never reaches the cause of your need' },
  { id: 'cost', label: 'the cost', hint: 'the cost: what happens to the user, or to people around them, if your need stays unmet this week' },
  { id: 'met', label: 'what "met" looks like', hint: 'what "met" looks like: one observable condition that would move you to 0' },
  { id: 'step', label: 'smallest next step', hint: 'the smallest next step: one action in the next 24 hours that would start to meet your need' },
  { id: 'picture', label: 'a picture', hint: 'a quick image or comparison that makes your need click for the others, followed by the concrete ask' },
];

const SOCIETY_STYLES = [
  'wellness platitude (yoga, deep breathing, a bubble bath, a walk)',
  'rest instead of acting ("sleep on it", "take a nap, you\'ll feel better")',
  'minimizing ("it\'s not a big deal", "you\'re overthinking it")',
  'toxic positivity ("just stay positive", "look on the bright side")',
  'hustle ("everyone\'s busy, just push through", "that\'s adulting")',
  'keep the peace ("don\'t rock the boat", "just let it go")',
  'effort-shaming ("that seems like a lot of effort, are you sure?")',
  'comparison ("others have it way worse")',
  'treat yourself ("buy something nice, you deserve it")',
  'time fixes it ("it\'ll sort itself out")',
];

export const MOVE_LABELS = {
  advocate: 'states its need',
  pushback: 'pushes back',
  answer: 'answers',
  support: 'offers help',
  accept: 'can live with it',
  comeback: 'comes back to its need',
  question: 'asks',
  callout: 'calls out Society',
  spotlight: 'points at who hurts most',
};
const BID_MOVES = ['advocate', 'pushback', 'answer', 'support', 'accept', 'comeback', 'question'];

// ---------- text helpers ----------

export function parseJSON(text) {
  const t = String(text ?? '').trim();
  const tries = [t];
  const fence = t.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fence) tries.push(fence[1]);
  const a = t.search(/[{[]/);
  const b = Math.max(t.lastIndexOf('}'), t.lastIndexOf(']'));
  if (a >= 0 && b > a) tries.push(t.slice(a, b + 1));
  for (const s of tries) {
    try { return JSON.parse(s); } catch { /* try the next shape */ }
  }
  return undefined;
}

export function sentences(text) {
  return String(text ?? '')
    .replace(/\s+/g, ' ')
    .trim()
    .split(/(?<=[.!?…]["”’)\]]?)\s+(?=["“‘'(\[]?[A-Z0-9])/)
    .filter((s) => /\w/.test(s));
}

const NAME_PREFIX = new RegExp(
  '^\\s*(?:\\[\\d+\\]\\s*)?(?:\\p{Extended_Pictographic}\\uFE0F?(?:\\u200D\\p{Extended_Pictographic}\\uFE0F?)*\\s*)?(?:' +
    Object.values(VOICES).filter((v) => v.id !== 'user').map((v) => v.name).join('|') +
    ')(?:\\s*(?:→|->|to)\\s*[^:]{1,30})?\\s*[:：]\\s*',
  'iu',
);

export function cleanText(text) {
  let t = String(text ?? '')
    .replace(/\r?\n+/g, ' ')
    .replace(/\*\*|__|`/g, '')
    .replace(/^\s*(?:[-*•]|#+)\s+/, '')
    .replace(/\s+/g, ' ')
    .trim();
  t = t.replace(NAME_PREFIX, '').replace(/\s*\[(?:msg |message |step )?\d+\]/gi, '').replace(/\b(?:msg|message) \d+\b/gi, 'earlier');
  if (/^["“].*["”]$/.test(t) && !/["“”]/.test(t.slice(1, -1))) t = t.slice(1, -1).trim();
  return t;
}

// Chat tics the UI already covers: "Fear here." and a leading "Consciousness," (the bubble shows who it's to).
function stripTics(text, speaker) {
  let t = text;
  const me = VOICES[speaker]?.name;
  if (me) t = t.replace(new RegExp(`^(?:${me} here[.:,!]?|I'?m ${me}(?:,| and|:)(?: and)?)\\s+`, 'i'), '');
  t = t.replace(/^Consciousness,\s+/, '');
  return t.charAt(0).toUpperCase() + t.slice(1);
}

function clip(text, n) {
  const t = String(text ?? '');
  return t.length > n ? t.slice(0, n - 1).trimEnd() + '…' : t;
}

function shingles(text) {
  const words = String(text).toLowerCase().match(/[a-z0-9']+/g) || [];
  const set = new Set();
  for (let i = 0; i + 2 < words.length; i++) set.add(`${words[i]} ${words[i + 1]} ${words[i + 2]}`);
  return set;
}

// Share of `a`'s word triples that already appear in `b` (0..1).
export function overlap(a, b) {
  const A = shingles(a);
  const B = shingles(b);
  if (A.size < 4) return 0;
  let n = 0;
  for (const x of A) if (B.has(x)) n++;
  return n / A.size;
}

const HARSH = /\b(idiot|stupid|moron|jerk|asshole|loser|bad person|terrible person|shut up|worthless|incompetent|screw (?:him|her|them|you))\b/i;

const QUOTE = /(?<=^|[\s:(—-])["“'‘]([^"“”‘’]{20,}?)["”'’](?=[\s.,;:!?)]|$)/g;
// A quoted message to someone: "text her: '…'", "send '…'", "say '…'".
const SCRIPT = /\b(?:text(?:ing)?|send(?:ing)?|say(?:ing)?|tell(?:ing)? (?:him|her|them)|messag(?:e|ing)|email(?:ing)?|reply(?:ing)?|ask(?:ing)?)\b[^"“'‘.]{0,40}?["“'‘]([^"“”‘’]{15,}?)["”'’](?=[\s.,;:!?)]|$)/gi;
const norm = (q) => q.toLowerCase().replace(/[^a-z0-9 ]/g, '').replace(/\s+/g, ' ').trim();

// Scripts (8+ quoted words) this text re-quotes from an earlier message.
export function copiedQuotes(text, earlier = []) {
  const theirs = earlier.flatMap((e) => [...String(e.text).matchAll(QUOTE)].map((m) => ({ q: norm(m[1]), who: e.who })));
  const out = [];
  for (const m of String(text).matchAll(QUOTE)) {
    const q = norm(m[1]);
    if (q.split(' ').length < 8) continue;
    const hit = theirs.find((t) => t.q.split(' ').length >= 6 && (t.q === q || t.q.includes(q) || q.includes(t.q)));
    if (hit) out.push({ span: m[0], quote: q, who: hit.who });
  }
  return out;
}

export function checkMessage(text, earlier = [], speaker = '') {
  const problems = [];
  const me = VOICES[speaker];
  if (me) {
    const other = Object.values(VOICES).find((v) => v.id !== speaker && v.id !== 'user' && new RegExp(`\\bI'?m (?:the )?${v.name}\\b|\\bI am (?:the )?${v.name}\\b`, 'i').test(text));
    if (other) problems.push(`It speaks as ${other.name}. You are ${me.name}; speak only as yourself.`);
    if (new RegExp(`^${me.name}\\b`, 'i').test(text)) problems.push(`It opens with your own name. Don't address or name yourself.`);
  }
  const copy = copiedQuotes(text, earlier)[0];
  if (copy) {
    problems.push(copy.who === speaker || !VOICES[copy.who]
      ? `It re-quotes your own earlier script ("${clip(copy.quote, 80)}"). Refer to it as "my earlier text" and say only what changed.`
      : `It re-quotes ${VOICES[copy.who].name}'s script ("${clip(copy.quote, 80)}"). Write "+1 to ${VOICES[copy.who].name}'s text" instead and add only what your own angle changes.`);
  }
  const n = sentences(text).length;
  if (n > 6) problems.push(`It has ${n} sentences. The hard limit is 6; aim for 2-4.`);
  const words = text.split(/\s+/).length;
  if (words > 95) problems.push(`It has ${words} words. Keep it under 80 so it fits a chat bubble.`);
  if (HARSH.test(text)) problems.push('It uses a harsh or insulting word. Stay firm but radically non-violent.');
  for (const e of earlier) {
    if (overlap(text, e.text) > 0.4) {
      problems.push(`It repeats an earlier message too closely: "${clip(e.text, 160)}". Say something new, with new words and a new angle.`);
      break;
    }
  }
  return problems;
}

const STOP = new Set('a an the and or but to of in on at by for with my me i we our you your it its is are be was this that what would move 0 need needs plan step until before after from so if then just only still also not no'.split(' '));
const words = (t) => (String(t).toLowerCase().match(/[a-z0-9']+/g) || []).filter((w) => w.length > 2 && !STOP.has(w));

// True when most of a need's content words already appear in the plan.
export function covered(need, steps) {
  const w = [...new Set(words(need))];
  if (w.length < 3) return false;
  const plan = new Set(words(steps.join(' ')));
  return w.filter((x) => plan.has(x)).length / w.length >= 0.7;
}

// Time frame the user set, so plans don't drift to "tonight" or "tomorrow".
export function timeFrame(text) {
  const t = String(text).toLowerCase();
  const hit = [['right now', 'right now'], ['this morning', 'this morning'], ['this afternoon', 'this afternoon'], ['tonight', 'tonight'],
    ['today', 'today'], ['tomorrow', 'tomorrow'], ['this weekend', 'this weekend'], ['all weekend', 'this weekend'], ['next week', 'next week']]
    .find(([k]) => t.includes(k));
  return hit ? hit[1] : '';
}
const SAME_DAY = ['right now', 'this morning', 'this afternoon', 'tonight', 'today'];

function capFirst(t) {
  return t ? t.charAt(0).toUpperCase() + t.slice(1) : t;
}

function trimToSentences(text, max) {
  const s = sentences(text);
  return s.length > max ? s.slice(0, max).join(' ') : text;
}

function resolveId(x) {
  const k = String(x ?? '').toLowerCase().replace(/[^a-z]/g, '');
  if (!k) return '';
  if (VOICES[k]) return k;
  if (k === 'theuser' || k === 'me') return 'user';
  const hit = Object.values(VOICES).find((v) => v.name.toLowerCase() === k);
  return hit ? hit.id : '';
}

const label = (id) => (VOICES[id] ? `${VOICES[id].emoji} ${VOICES[id].name}` : id);
const asScore = (v, fallback) => (v === 0 || v === '0' ? 0 : v === -1 || v === '-1' ? -1 : fallback);

// ---------- prompt pieces ----------

const FRAME = `This is the inner group chat of one person (the user), based on their Teffy framework for decision-making. The voices:
- 🧠 Consciousness: the user's decision-maker. It owns the plan and keeps updating it from what the emotions say.
- 16 emotions, each a separate voice with its own need. An emotion's score is -1 (the plan does not meet its need, so it suffers) or 0 (it can live with the plan, even grudgingly). There is no +1.
- 🦜 Society: not an emotion and never scored. It parrots well-meaning, generic advice the user absorbed from people and culture without checking it against their needs. Its advice never enters the plan.
The goal is begrudging acceptance: every emotion reaches 0 through real negotiation, never fake agreement. ❤️ Sadness speaks up for the emotion that has been heard least.
House facts: Overwhelm never negotiates; respect its limit by shrinking the plan, never by persuading it. Tiredness is easily bullied by Impulsivity. Impulsivity can pull Doubt out of loops. Boredom and Overwhelm usually pull opposite ways.`;

const RULES = `HOW EVERY CHAT MESSAGE MUST READ
1. One paragraph that fits a phone chat bubble: usually 2-4 sentences, never more than 6. No line breaks, lists, or headings. Don't start with your own name.
2. Radically non-violent and pro-human. No insults, labels, blame, or sarcasm at anyone's expense, and never "tell them they're a bad person". Firm, never harsh: toward the user, other people, and the other voices here.
3. Hyper-precise and actionable. Name the specific barrier, then a doable request: who does what, by when. When you propose a NEW message to someone, write the actual words in quotes. If a script already exists in the chat or the plan, refer to it ("Embarrassment's text") and say only what to change.
4. Use only facts the user gave. Never invent counts, dates, weekdays, times, history, or what someone said. Use a [placeholder] for names and facts only the user knows; a placeholder the user will fill in counts as covered, so don't stay at -1 over a blank. For a time, amount, or limit the plan depends on, propose a concrete default the user can change ("lights out 11pm", "keep 6 months of rent saved"). Keep the user's time frame: if they said "now" or "this morning", every step happens from now, today, unless the user chose otherwise. Details in someone's example script are placeholders, not facts.
5. If your need is already in the current plan, say you can live with it instead of asking again.
6. Humor or slang ("lol that sucks", "bro") is welcome only if the same message says what you mean by it and what you want the Consciousness to do.
7. A question must say why you are asking and what answer would settle it. No dithering ("should we? idk"): name what is unknown or feared, and what would settle it.
8. Never repeat yourself or copy anyone. If your need is still unmet you may come back to it, but with new words and a new angle, saying exactly what the current advice leaves untouched.
9. Don't re-propose a fix someone already proposed, and don't re-quote their script. If you back it, say so in a few words ("+1 to Overwhelm's ask") and add only what your own angle contributes.
10. Speak as yourself in the first person ("I need…"), never about yourself in the third person, and never as another voice ("I'm Fear"). You don't have to open by naming who you're talking to.
11. Argue only from YOUR need as defined above. Mention another emotion at most in one clause, to say how its need touches yours.
Too vague: "That doesn't help my boundaries."
Precise: "Deep breathing calms me for a minute, but Thursday's band practice still lands on my climbing night and the drummer still doesn't know it bugs me. What would move me to 0 is texting '[Drummer], can we move practice to Wednesdays from next week?' tonight."`;

const rosterLine = (e) => `${e.id}: ${e.emoji} ${e.name}. -1 when ${e.minus}. Needs: ${e.need}`;

function persona(e) {
  return `YOU ARE ${e.emoji} ${e.name.toUpperCase()}.
Motto: "${e.motto}". You go to -1 when ${e.minus}.
Purpose: ${e.purpose}
To satisfy your need: ${e.need}
Personality: ${e.personality}
Voice: ${e.voice}`;
}

// ---------- the conversation ----------

function freshState() {
  return {
    thought: '',
    followups: [],
    plan: { version: 0, steps: [], paths: false, final: false },
    scores: {}, // id -> {score, need, why}
    spotlight: '',
    messages: [], // {n, who, text, to, move, score, lens}
    ledger: [], // turned-down advice {advice, from, by, why}
    societyLines: [], // {text, to, style}
    lensesUsed: {},
    prefs: {},
    queue: [],
    roundCount: 0,
    acceptRun: 0,
    locks: {}, // id -> the need that, once met, moved it to 0
    waiting: {}, // id -> turns it asked to speak and wasn't picked
    pendingOpen: false,
    phase: 'idle', // idle | running | wrapped
    usage: { calls: 0, inChars: 0, outChars: 0, byKind: {} },
  };
}

export class Conversation {
  constructor({ ask, settings = {}, onEvent = () => {}, random = Math.random, state, events } = {}) {
    this.ask = ask;
    this.settings = { ...DEFAULT_SETTINGS, ...settings };
    this.onEvent = onEvent;
    this.random = random;
    const fresh = freshState();
    const old = state ? structuredClone(state) : {};
    this.s = { ...fresh, ...old, plan: { ...fresh.plan, ...old.plan }, usage: { ...fresh.usage, ...old.usage, byKind: { ...old.usage?.byKind } } };
    this.events = events ? [...events] : [];
    this.signal = undefined;
  }

  toJSON() {
    return { settings: this.settings, state: this.s, events: this.events };
  }

  emit(ev) {
    const e = { ...ev, at: this.events.length };
    if (!['typing', 'deciding', 'usage'].includes(e.type)) this.events.push(e);
    this.onEvent(e, this);
  }

  // ----- public API -----

  async start(thought, { signal } = {}) {
    const s = this.s;
    s.thought = String(thought).trim();
    s.messages.push({ n: s.messages.length + 1, who: 'user', text: s.thought });
    this.emit({ type: 'user', text: s.thought });
    s.pendingOpen = true;
    s.phase = 'running';
    return this.run(signal);
  }

  async followUp(text, { signal } = {}) {
    const s = this.s;
    const t = String(text).trim();
    s.followups.push(t);
    s.messages.push({ n: s.messages.length + 1, who: 'user', text: t });
    this.emit({ type: 'user', text: t });
    s.queue = [{ who: 'consciousness', followup: t }];
    s.roundCount = 0;
    s.acceptRun = 0;
    s.phase = 'running';
    return this.run(signal);
  }

  // Resume after an error or a Stop.
  async resume({ signal } = {}) {
    if (this.s.phase !== 'running') return { ok: true };
    return this.run(signal);
  }

  async wrapUp({ signal } = {}) {
    if (this.s.phase !== 'running') return { ok: true };
    this.signal = signal;
    try {
      await this.wrap();
      return { ok: true };
    } catch (err) {
      return this.fail(err);
    }
  }

  async run(signal) {
    this.signal = signal;
    try {
      if (this.s.pendingOpen) await this.open();
      while (this.s.phase === 'running') {
        if (signal?.aborted) throw { code: 'cancelled', message: 'Stopped.' };
        await this.step();
      }
      return { ok: true };
    } catch (err) {
      return this.fail(err);
    }
  }

  fail(err) {
    const code = err?.code || 'upstream_error';
    const message = err?.message || String(err);
    this.emit({ type: 'error', code, message });
    return { ok: false, code, message };
  }

  // ----- turn logic -----

  lastMsg() {
    return this.s.messages[this.s.messages.length - 1];
  }

  countBy(id) {
    return this.s.messages.filter((m) => m.who === id).length;
  }

  // Emotion messages since the Consciousness (or the user) last spoke.
  emoSince() {
    let n = 0;
    for (let i = this.s.messages.length - 1; i >= 0; i--) {
      const m = this.s.messages[i];
      if (m.who === 'consciousness' || m.who === 'user') break;
      if (BY_ID[m.who]) n++;
    }
    return n;
  }

  tracked() {
    return Object.keys(this.s.scores);
  }

  setScore(id, score, extra = {}) {
    if (!BY_ID[id]) return;
    const prev = this.s.scores[id];
    const next = { score, need: prev?.need || '', why: prev?.why || '', ...extra };
    if (score === 0) next.need = extra.need ?? '';
    this.s.scores[id] = next;
    if (prev?.score === -1 && score === 0 && id !== 'sadness') this.s.locks[id] = prev.need || prev.why || '';
    if (score === -1) delete this.s.locks[id];
    if (prev && prev.score !== score && !this.quiet) this.emit({ type: 'score', id, from: prev.score, to: score });
  }

  // Sadness is -1 while its spotlighted emotion still suffers after the
  // Consciousness has had a chance to revise the plan.
  refreshSadness() {
    const s = this.s;
    const minus = this.tracked().filter((id) => id !== 'sadness' && s.scores[id].score === -1);
    const recent = (id) => s.messages.slice(-8).filter((m) => m.who === id).length;
    const spokeJustNow = s.messages.slice(-3).some((m) => m.who === s.spotlight);
    if (!s.spotlight || s.scores[s.spotlight]?.score !== -1 || (spokeJustNow && minus.length > 1)) {
      const pick = [...minus].sort((a, b) => recent(a) - recent(b) || this.countBy(a) - this.countBy(b))[0] || '';
      if (pick !== s.spotlight) {
        // Announce a new spotlight only when the last one was actually looked after.
        const resolved = !s.spotlight || s.scores[s.spotlight]?.score === 0;
        s.spotlight = pick;
        if (pick && resolved) this.emit({ type: 'spotlight', id: pick });
      }
    }
    const want = s.spotlight && s.plan.version >= 2 && s.scores[s.spotlight]?.score === -1 ? -1 : 0;
    if (s.scores.sadness || want === -1) {
      this.setScore('sadness', want, { need: want === -1 ? `make ${VOICES[s.spotlight].name} a 0` : '' });
    }
  }

  roundCap() {
    const max = this.settings.maxMessages;
    return this.s.followups.length ? Math.max(8, Math.round(max * 0.6)) : max;
  }

  needsConsciousness() {
    const last = this.lastMsg();
    if (!last || last.who === 'society') return false;
    if (BY_ID[last.who] && last.to === 'consciousness' && last.move === 'question') return true;
    return this.emoSince() >= 3;
  }

  async step() {
    const s = this.s;
    const last = this.lastMsg();
    const cap = this.roundCap();
    if (s.roundCount >= cap && last?.who !== 'society') {
      const open = last && BY_ID[last.who] && last.to === 'consciousness' && last.move === 'question';
      return open && !s.queue.length ? this.consciousness({}) : this.wrap();
    }

    const queued = s.queue[0] || null;
    let act = queued;
    let bids = null;
    if (!act) {
      if (last?.who === 'society') {
        // Society's advice always gets called out: usually by the emotion it was
        // aimed at, sometimes by another suffering emotion whose angle sees the miss.
        const others = this.tracked().filter((id) => id !== last.to && id !== 'sadness' && s.scores[id].score === -1 &&
          !s.messages.slice(-4).some((m) => m.who === id));
        const caller = others.length && this.random() < 0.35 ? others[Math.floor(this.random() * others.length)] : last.to;
        act = { id: caller, move: 'callout', to: 'society', why: 'Society just talked past a real need' };
      } else if (this.needsConsciousness()) act = { who: 'consciousness' };
      else {
        bids = await this.floor();
        act = this.pick(bids);
        const sinceUser = s.messages.slice(s.messages.map((m) => m.who).lastIndexOf('user') + 1);
        const quiet = !sinceUser.some((m) => BY_ID[m.who]);
        const minus = this.tracked().filter((id) => id !== 'sadness' && s.scores[id].score === -1);
        if ((!act || act === 'wrap') && quiet && minus.length) {
          const id = minus.sort((a, b) => this.countBy(a) - this.countBy(b))[0];
          act = { id, move: this.countBy(id) ? 'comeback' : 'advocate', to: '', why: 'nobody has said it yet' };
        }
        if (act === 'wrap') {
          this.emit({ type: 'bids', bids, pick: '' });
          return this.wrap();
        }
        if (!act) {
          this.emit({ type: 'bids', bids, pick: '' });
          if (last?.who === 'consciousness') return this.wrap();
          act = { who: 'consciousness' };
        } else {
          this.emit({ type: 'bids', bids, pick: act.id });
        }
        for (const b of bids) {
          if (b.act === 'reply' && b.id !== act?.id) s.waiting[b.id] = (s.waiting[b.id] || 0) + 1;
        }
      }
    }

    if (act.who === 'consciousness') await this.consciousness(act);
    else if (act.who === 'society') await this.society(act);
    else await this.speak(act);
    if (queued) {
      const i = s.queue.indexOf(queued);
      if (i >= 0) s.queue.splice(i, 1);
    }
  }

  pick(bids) {
    const s = this.s;
    const last = this.lastMsg();
    // A Society line is called out once, right after it lands; later "callout"
    // bids become ordinary pushback or a return to the emotion's own need.
    const reply = bids
      .filter((b) => b.act === 'reply' && b.id !== last?.who)
      .map((b) => (b.move !== 'callout' ? b : { ...b, move: BY_ID[b.to] ? 'pushback' : this.countBy(b.id) ? 'comeback' : 'advocate', to: BY_ID[b.to] ? b.to : '' }));

    const minus = this.tracked().filter((id) => s.scores[id].score === -1);
    if (minus.length === 0) {
      const accepts = reply.filter((b) => b.move === 'accept' && this.lastScoreSaid(b.id) === -1);
      if (accepts.length && s.acceptRun < 2) {
        s.acceptRun++;
        return { ...accepts.sort((a, b) => this.countBy(a.id) - this.countBy(b.id))[0], move: 'accept' };
      }
      return 'wrap';
    }

    // Sadness names the most neglected emotion once a few voices have spoken.
    const emoMsgs = s.messages.filter((m) => BY_ID[m.who]).length;
    const sadnessLast = s.messages.map((m) => m.who).lastIndexOf('sadness');
    const sadnessThisPlan = s.sadnessPlan === s.plan.version;
    const spotSpoke = s.messages.slice(-2).some((m) => m.who === s.spotlight);
    const sadnessDue = s.spotlight && !sadnessThisPlan && !spotSpoke && last?.who !== 'sadness' &&
      minus.filter((id) => id !== 'sadness').length >= 2 &&
      ((sadnessLast < 0 && emoMsgs >= 2) || (sadnessLast >= 0 && s.scores.sadness?.score === -1));
    const sad = reply.findIndex((b) => b.id === 'sadness');
    if (sad >= 0 && (sadnessThisPlan || spotSpoke || !s.spotlight)) reply.splice(sad, 1);
    else if (sad >= 0) reply[sad] = { ...reply[sad], move: 'spotlight', to: s.spotlight };
    if (sadnessDue && !reply.some((b) => b.id === 'sadness')) {
      reply.push({ id: 'sadness', act: 'reply', move: 'spotlight', to: s.spotlight, why: `${VOICES[s.spotlight].name} has barely been heard`, injected: true });
    }
    if (!reply.length) return null;

    if (last && BY_ID[last.to]) {
      const b = reply.find((x) => x.id === last.to);
      if (b) return { ...b, move: ['support', 'advocate'].includes(b.move) ? 'answer' : b.move };
    }

    const lastIdx = (id) => s.messages.map((m) => m.who).lastIndexOf(id);
    const justRevised = last?.who === 'consciousness';
    const weight = (b) => {
      const spoken = this.countBy(b.id);
      const base = { pushback: 6, answer: 6, callout: 6, spotlight: 5, advocate: 4, question: 3, comeback: 3, support: 2, accept: 2 }[b.move] ?? 2;
      let w = base + (s.scores[b.id]?.score === -1 ? 1 : 0) + (spoken === 0 ? 2 : 0) - spoken;
      if (b.move === 'accept' && justRevised) w += 3;
      if (b.move === 'comeback' && !justRevised) w -= 1;
      if (b.id === 'sadness' && sadnessDue) w += 2;
      if (s.messages.length - lastIdx(b.id) <= 2) w -= 3;
      w += 1.5 * (s.waiting[b.id] || 0); // waiting your turn earns the floor
      if (b.move === 'question' && (s.waiting[b.id] || 0) >= 2) w += 2;
      const cap = this.roundCap();
      if (s.roundCount >= cap - 2 && ['advocate', 'question'].includes(b.move)) w -= 4; // no new threads at the very end
      return w;
    };
    const ranked = reply
      .map((b) => ({ b, w: weight(b) }))
      .sort((x, y) => y.w - x.w || lastIdx(x.b.id) - lastIdx(y.b.id));
    const top = ranked[0].b;
    const move = top.move === 'advocate' && this.countBy(top.id) > 0 ? 'comeback' : top.move;
    return { ...top, move };
  }

  lastScoreSaid(id) {
    for (let i = this.s.messages.length - 1; i >= 0; i--) {
      const m = this.s.messages[i];
      if (m.who === id) return m.score;
    }
    return -1;
  }

  maybeSociety(msg) {
    const s = this.s;
    const mode = this.settings.society;
    if (mode === 'off' || msg.score !== -1 || ['accept', 'callout', 'spotlight'].includes(msg.move)) return;
    if (s.societyLines.length >= (mode === 'often' ? 3 : 2)) return;
    if (s.roundCount > this.roundCap() - 3) return;
    const emoMsgs = s.messages.filter((m) => BY_ID[m.who]).length;
    if (emoMsgs < 2) return;
    const lastSociety = s.messages.map((m) => m.who).lastIndexOf('society');
    if (lastSociety >= 0 && s.messages.length - lastSociety < 5) return;
    const p = mode === 'often' ? 0.8 : 0.45;
    const overdue = s.societyLines.length === 0 && emoMsgs >= 3;
    if (overdue || this.random() < p) s.queue.unshift({ who: 'society', to: msg.who });
  }

  // ----- model calls -----

  async call(kind, prompt) {
    const s = this.s;
    let ctl;
    let unlink = () => {};
    if (this.signal) {
      if (this.signal.aborted) throw { code: 'cancelled', message: 'Stopped.' };
      ctl = new AbortController();
      const onAbort = () => ctl.abort();
      this.signal.addEventListener('abort', onAbort, { once: true });
      unlink = () => this.signal.removeEventListener('abort', onAbort);
    }
    try {
      const res = await this.ask(prompt, { signal: ctl?.signal, kind, settings: this.settings });
      const text = typeof res === 'string' ? res : res?.text ?? '';
      s.usage.calls++;
      s.usage.inChars += prompt.length;
      s.usage.outChars += text.length;
      s.usage.byKind[kind] = (s.usage.byKind[kind] || 0) + 1;
      if (res && typeof res === 'object' && res.modelApplied === undefined && res.modelTierApplied) s.usage.tierOnly = true;
      this.emit({ type: 'usage', usage: s.usage });
      return text;
    } finally {
      unlink();
    }
  }

  // Ask for JSON; one retry when the reply doesn't parse or validate.
  async callJSON(kind, prompt, valid) {
    let text = await this.call(kind, prompt);
    let v = parseJSON(text);
    if (valid(v)) return v;
    text = await this.call(kind, `${prompt}\n\nYour previous reply could not be read as the JSON object described above. Reply with only that JSON object, nothing else.`);
    v = parseJSON(text);
    return valid(v) ? v : null;
  }

  // JSON whose `text` field is a chat message: also retry once on length,
  // harshness, or repetition, then hard-trim whatever comes back.
  async callMessage(kind, prompt, valid, earlier, speaker = '') {
    let v = await this.callJSON(kind, prompt, valid);
    if (!v) return null;
    let text = cleanText(v.text);
    const problems = checkMessage(text, earlier, speaker);
    if (problems.length) {
      const fix = `${prompt}\n\nYOUR DRAFT MESSAGE WAS: "${text}"\nIt has these problems:\n- ${problems.join('\n- ')}\nWrite a corrected version. Reply with only the JSON object.`;
      const v2 = await this.callJSON(kind, fix, valid);
      if (v2) {
        v = v2;
        text = cleanText(v2.text);
      }
    }
    // Still re-quoting someone's script after the rewrite: point at it instead.
    for (const c of copiedQuotes(text, earlier)) {
      const parts = sentences(text);
      const kept = parts.filter((x) => !norm(x).includes(c.quote.slice(0, 40)));
      const owner = VOICES[c.who] && c.who !== speaker ? `+1 to ${VOICES[c.who].name}'s text.` : '';
      text = kept.length && kept.length < parts.length ? [...kept, owner].filter(Boolean).join(' ') : text;
    }
    v.text = trimToSentences(stripTics(text, speaker), 6);
    return v;
  }

  // ----- shared context blocks -----

  situation() {
    const s = this.s;
    let t = `THE USER SAID: "${s.thought}"`;
    for (const f of s.followups) t += `\nTHE USER LATER ADDED: "${f}"`;
    const tf = timeFrame([s.thought, ...s.followups].join(' '));
    if (tf) t += `\nTIME FRAME (set by the user): ${tf}. Every step happens in that time frame${SAME_DAY.includes(tf) ? ', starting from now' : ''}; don't move it to another day.`;
    return t;
  }

  planBlock() {
    const p = this.s.plan;
    if (!p.steps.length) return 'CURRENT PLAN: none yet.';
    const head = p.paths
      ? `CURRENT PLAN v${p.version}: two paths are on the table; the emotions are weighing them.`
      : `CURRENT PLAN v${p.version}${p.final ? ' (agreed at the last wrap-up)' : ''}, owned by 🧠 Consciousness:`;
    return `${head}\n${p.steps.map((x) => `- ${x}`).join('\n')}`;
  }

  standings() {
    const s = this.s;
    const ids = this.tracked();
    const lines = ids.map((id) => {
      const sc = s.scores[id];
      return `- ${label(id)}: ${sc.score}${sc.score === -1 && sc.need ? `, needs: ${sc.need}` : sc.score === -1 && sc.why ? ` ("${sc.why}")` : ''}`;
    });
    if (s.spotlight) lines.push(`Sadness's spotlight (most neglected right now): ${label(s.spotlight)}`);
    lines.push(ids.length ? 'Every emotion not listed: 0 so far.' : 'No scores yet.');
    return `WHERE EVERYONE STANDS\n${lines.join('\n')}`;
  }

  ledgerBlock() {
    const s = this.s;
    const lines = s.ledger.map((a) => `- "${a.advice}" (offered by ${label(a.from)}; ${label(a.by)} turned it down${a.why ? `: ${clip(a.why, 120)}` : ''})`);
    for (const l of s.societyLines) lines.push(`- 🦜 Society's "${clip(l.text, 120)}" (Society advice never enters the plan)`);
    return `ADVICE ALREADY TURNED DOWN (never re-offer it; build past it)\n${lines.length ? lines.join('\n') : '- none yet'}`;
  }

  chatBlock(limit = 26) {
    const msgs = this.s.messages.slice(-limit);
    const lines = msgs.map((m) => {
      const who = m.who === 'user' ? '🙋 The user' : label(m.who);
      const to = m.to && VOICES[m.to] && m.to !== 'user' ? ` → ${VOICES[m.to].name}` : '';
      const score = BY_ID[m.who] && m.score !== undefined ? ` (${m.score})` : '';
      return `${who}${to}${score}: ${m.text}`;
    });
    return `CHAT SO FAR (oldest first)\n${lines.join('\n')}`;
  }

  context() {
    return [this.situation(), this.planBlock(), this.standings(), this.ledgerBlock(), this.chatBlock()].join('\n\n');
  }

  // Plan steps must stand on their own: "send Embarrassment's text" becomes the actual words,
  // but only when that emotion really drafted a message to someone; otherwise the step stays as written.
  resolveRefs(step) {
    const names = Object.values(VOICES).filter((v) => v.id !== 'user').map((v) => v.name).join('|');
    return step.replace(new RegExp(`\\b(${names})'s (?:earlier |exact |drafted )?(?:text|message|script|email|draft|wording)\\b`, 'g'), (whole, who) => {
      const id = resolveId(who);
      for (const m of [...this.s.messages].reverse()) {
        if (m.who !== id) continue;
        for (const q of m.text.matchAll(SCRIPT)) return `"${q[1]}"`;
      }
      return whole;
    });
  }

  // ----- phases -----

  async open() {
    const s = this.s;
    this.emit({ type: 'typing', who: 'consciousness' });
    const prompt = `${FRAME}

${this.situation()}

THE 16 EMOTIONS
${EMOTIONS.map(rosterLine).join('\n')}

TASK: Start the chat.
1. "plan": As 🧠 Consciousness, restate the user's first idea as a plan in one sentence, the way they first pictured it. It is optimistic and may overlook objections.
2. "text": The Consciousness's opening chat message, 1-2 sentences, putting that plan to the emotions with a bit too much confidence, in your own words (no stock phrases like "Good news, everyone" or "lock it in").
3. "minus": Consider all 16 emotions. List ONLY those that honestly score -1 to this first plan, each with a hint of 15 words or fewer in that emotion's own voice. Don't invent a -1 that doesn't fit an emotion's profile, and don't hide a real one. Usually 3-6.
4. "spotlight": As ❤️ Sadness, the id of the single emotion that is most neglected or suffering most.

Reply with only this JSON:
{"plan": "...", "text": "...", "minus": [{"id": "<emotion id>", "why": "..."}], "spotlight": "<emotion id>"}`;
    const v = await this.callJSON('open', prompt, (x) => x && typeof x.plan === 'string' && Array.isArray(x.minus));
    const plan = cleanText(v?.plan || s.thought);
    const text = cleanText(v?.text || `Here's the plan: ${plan} Who's in?`);
    const minus = [];
    for (const m of v?.minus || []) {
      const id = resolveId(m?.id);
      if (!BY_ID[id] || id === 'sadness' || minus.some((x) => x.id === id)) continue;
      minus.push({ id, why: cleanText(m.why) });
      s.scores[id] = { score: -1, need: '', why: cleanText(m.why) };
    }
    const spot = resolveId(v?.spotlight);
    s.spotlight = s.scores[spot]?.score === -1 ? spot : minus[0]?.id || '';
    s.plan = { version: 1, steps: [plan], paths: false, final: false };
    s.messages.push({ n: s.messages.length + 1, who: 'consciousness', text, to: '', move: 'open' });
    s.pendingOpen = false;
    this.emit({ type: 'opening', text, plan: s.plan, minus, spotlight: s.spotlight });
  }

  async floor() {
    const s = this.s;
    this.emit({ type: 'deciding' });
    const last = this.lastMsg();
    // Scores only move when the plan (or the user's situation) changes; other
    // turns just decide who talks, which keeps the call small and the board steady.
    const rescore = (last?.who === 'consciousness' && last.move !== 'open') || last?.who === 'user';
    let focus = '';
    if (last?.who === 'consciousness' && last.move === 'paths') {
      focus = '\nThe Consciousness just offered Path A and Path B. Every bid includes "prefers": "A" or "B", and scores the path that emotion prefers.';
    } else if (last?.who === 'consciousness') {
      focus = '\nThe Consciousness just revised the plan. Re-score every emotion against the new plan; those it now satisfies may "accept", those it still misses may "comeback" with a new angle.';
    } else if (last?.who === 'user') {
      focus = '\nThe user just added something. Re-score against it.';
    }
    const counts = EMOTIONS.map((e) => [e, this.countBy(e.id)]).filter(([, n]) => n > 0)
      .map(([e, n]) => `${e.name} ${n}`).join(', ');
    const scoreRule = rescore
      ? `- "score": its honest reaction to the CURRENT PLAN as written (not to suggestions the Consciousness hasn't adopted yet). 0 only if the plan concretely covers its need as it last stated it; never 0 to force agreement. Any emotion can newly drop to -1 if the plan creates a problem for it.\n`
      : '';
    const prompt = `${FRAME}

${this.context()}
Messages so far per emotion: ${counts || 'none yet'}.
Last message: from ${last ? label(last.who) : 'nobody'}${last?.to && VOICES[last.to] ? ` to ${label(last.to)}` : ''}.${focus}

THE 16 EMOTIONS
${EMOTIONS.map(rosterLine).join('\n')}

TASK: You are the chat's turn-taker, not a speaker. Right after the last message, each emotion privately decides whether to chime in or hold back, like people in a real group chat.
Give a bid for ${rescore ? 'every emotion currently at -1, plus' : ''} any emotion the latest message affects or that has something specific and new to add. At most 6 bids. Skip Sadness unless someone is being overlooked.
For each bid:
${scoreRule}- "act": "reply" only if it has something NEW to add right now; otherwise "hold". Usually only 1-3 emotions reply and the rest hold, like a real group chat. Good reasons to reply: its need hasn't been stated yet (advocate); advice aimed at it misses its need (pushback); someone asked it something (answer); it has concrete new help for another emotion from its own angle (support); the plan changed and it can now live with it (accept); its need is still unmet and it has a fresh angle (comeback); it needs an answer from someone (question). Agreeing with or repeating what was just said is a reason to hold, and so is an ask the current plan already covers.
- "move": one of advocate, pushback, answer, support, accept, comeback, question.
- "to": the id it would address (an emotion id or "consciousness"), or "".
- "why": 12 words or fewer, in its own voice: what it wants to contribute, or why it holds back.

Reply with only this JSON:
{"bids": [{"id": "<emotion id>", ${rescore ? '"score": -1, ' : ''}"act": "reply", "move": "advocate", "to": "", "why": "..."${s.plan.paths && rescore ? ', "prefers": "A"' : ''}}]}`;
    const v = await this.callJSON('floor', prompt, (x) => x && Array.isArray(x.bids));
    let bids = [];
    for (const b of v?.bids || []) {
      const id = resolveId(b?.id);
      if (!BY_ID[id] || bids.some((x) => x.id === id)) continue;
      const current = s.scores[id]?.score ?? 0;
      bids.push({
        id,
        score: rescore ? asScore(b.score, current) : current,
        act: b.act === 'reply' ? 'reply' : 'hold',
        move: BID_MOVES.includes(b.move) ? b.move : 'advocate',
        to: resolveId(b.to),
        why: cleanText(b.why),
        prefers: b.prefers === 'A' || b.prefers === 'B' ? b.prefers : undefined,
      });
    }
    if (!v) {
      // Fallback when the turn-taker's reply can't be read: suffering voices bid in order.
      bids = this.tracked().filter((id) => s.scores[id].score === -1 && id !== 'sadness').map((id) => ({
        id, score: -1, act: 'reply', move: this.countBy(id) ? 'comeback' : 'advocate', to: '', why: 'still at -1',
      }));
    }
    for (const b of bids) {
      if (!rescore && b.act === 'reply' && ['pushback', 'comeback'].includes(b.move) && b.id !== 'sadness' && s.scores[b.id]?.score === 0 && this.countBy(b.id) > 0 && !covered(b.why, s.plan.steps)) {
        b.score = -1;
        this.setScore(b.id, -1, { need: b.why });
      }
    }
    if (rescore) {
      const onlyPaths = last?.move === 'paths';
      for (const b of bids) {
        if (b.id === 'sadness') continue;
        if (b.prefers) s.prefs[b.id] = b.prefers;
        if (onlyPaths && b.score === 0 && s.scores[b.id]?.score === -1) { b.score = -1; continue; }
        if (b.score === -1 && s.scores[b.id]?.score === 0 && covered(b.why, s.plan.steps)) { b.score = 0; continue; }
        this.setScore(b.id, b.score);
      }
    }
    this.refreshSadness();
    return bids;
  }

  async speak(act) {
    const s = this.s;
    const e = BY_ID[act.id];
    if (!e) return;
    let move = e.id === 'sadness' ? 'spotlight' : act.move;
    if (move === 'advocate' && this.countBy(e.id) > 0) move = 'comeback';
    let lens = null;
    if (move === 'comeback') {
      // The angle this emotion hasn't used that the whole chat has used least.
      const used = s.lensesUsed[e.id] || [];
      const all = Object.values(s.lensesUsed).flat();
      const count = (id) => all.filter((x) => x === id).length;
      const fresh = LENSES.filter((l) => !used.includes(l.id));
      lens = (fresh.length ? fresh : LENSES).map((l, i) => [count(l.id) + this.random() * 0.5 + i * 0.01, l]).sort((a, b) => a[0] - b[0])[0][1];
    }
    const to = act.to && VOICES[act.to] ? act.to : '';
    const lastFrom = (id) => [...s.messages].reverse().find((m) => m.who === id);
    const toMsg = to ? lastFrom(to) : null;
    const toName = to ? label(to) : '';
    const myNeed = s.scores[e.id]?.need || s.scores[e.id]?.why || '';

    let task;
    switch (move) {
      case 'pushback':
        task = `${toName} said: "${toMsg?.text || ''}". It misses your need. Push back without dismissing ${toName}: say exactly what it leaves untouched and why it can't reach your need, then what would actually work.`;
        break;
      case 'callout': {
        const line = s.societyLines[s.societyLines.length - 1];
        const whose = 'YOUR own (not anyone else\'s)';
        task = `🦜 Society just said: "${line?.text}". Call it out in 2-3 sentences, kindly and precisely: name exactly what it leaves untouched in ${whose} need and what following it would cost here. Don't restate any ask or script already in the chat; it's on record. A little humor is fine if you explain it. Don't scold Society; just show why the advice falls short.`;
        break;
      }
      case 'answer':
        task = `${toName} said: "${toMsg?.text || ''}". Answer it directly from your own angle, then say what you need next if anything.`;
        break;
      case 'support': {
        const need = s.scores[to]?.need || s.scores[to]?.why || '';
        task = `Help ${toName || 'the emotion that needs it most'} from your own angle${need ? `; their need: "${need}"` : ''}. Offer one specific, doable move that nobody in the chat has offered yet and that also respects your own need.`;
        break;
      }
      case 'accept':
        task = `The plan changed. If plan v${s.plan.version} now covers your need, say which specific step moved you to 0 and any condition you're holding it to (grudging is fine), in 1-2 sentences, with score 0. If it still doesn't, say exactly what's missing instead and keep score -1.`;
        break;
      case 'comeback':
        task = `Your need is still not met by plan v${s.plan.version}. You may come back to it, but through a NEW angle: ${lens.hint}. Don't reuse your earlier wording. Say exactly what the current plan or the latest advice still leaves untouched.`;
        break;
      case 'question':
        task = `Ask the one question you most need answered${toName ? ` by ${toName}` : ''}. Say why you're asking and what answer would settle you.`;
        break;
      case 'spotlight':
        task = `You are Sadness, not the emotion you're pointing at; talk about it in the third person. In 2-3 sentences: name the single emotion heard least or hurting most right now (probably ${label(s.spotlight)}), say which plan step leaves it at -1 and why it keeps losing, show it care, and ask the Consciousness to fix that step. Don't restate its ask, write a script, or make a new proposal.`;
        break;
      default:
        task = `State your need. Say why you're at -1 with the plan as it stands: point at the exact part of the plan or situation that hurts you, and give the smallest concrete change that would move you to 0.`;
    }

    const mine = s.messages.filter((m) => m.who === e.id);
    const prompt = `${FRAME}

${persona(e)}

${this.context()}
${mine.length ? `\nYOUR EARLIER MESSAGES (don't reuse their wording or angle)\n${mine.map((m) => `- ${m.text}`).join('\n')}\n` : ''}${myNeed ? `\nYour current need: ${myNeed}\n` : ''}
YOUR TURN. You are ONLY ${e.name}. ${task}

${RULES}

Reply with only this JSON:
{"text": "<your chat message>", "to": "<who you address: an emotion id, consciousness, society, user (for a fact only the user knows), or empty>", "score": <-1 or 0: 0 only if CURRENT PLAN v${s.plan.version} already covers your need; your own proposal doesn't count until the Consciousness adopts it>, "need": "<if -1: what would move you to 0, 12 words or fewer; else empty>", "turns_down": "<if your message rejects someone's advice: a 2-6 word name for that advice; else empty>"${e.id === 'sadness' ? ', "spotlight": "<id of the emotion you named>"' : ''}}`;

    this.emit({ type: 'typing', who: e.id });
    const v = await this.callMessage('speak', prompt, (x) => x && typeof x.text === 'string' && x.text.trim().length > 0, s.messages.filter((m) => m.who !== 'user'), e.id);
    const text = v ? v.text : `I'm still at -1: ${myNeed || 'my need is not in the plan yet'}.`;
    const prev = s.scores[e.id]?.score;
    let score = e.id === 'sadness' ? (s.scores.sadness?.score ?? 0) : asScore(v?.score, prev ?? -1);
    const said = resolveId(v?.to);
    const msgTo = move === 'callout' ? 'society' : said && said !== e.id ? said : to;
    if (score === -1 && prev === 0 && covered(v?.need || '', s.plan.steps)) score = 0; // the plan already has it
    if (move === 'accept' && score === -1) move = 'comeback'; // "not there yet" isn't acceptance
    if (e.id === 'sadness') s.sadnessPlan = s.plan.version;
    s.waiting[e.id] = 0;
    if (e.id !== 'sadness') this.setScore(e.id, score, { need: score === -1 ? cleanText(v?.need) || myNeed : '' });
    if (e.id === 'sadness') {
      const spot = resolveId(v?.spotlight);
      if (BY_ID[spot] && spot !== 'sadness') s.spotlight = spot;
      if (!s.scores.sadness) s.scores.sadness = { score: 0, need: '', why: '' };
    }
    const declined = cleanText(v?.turns_down);
    if (declined && move !== 'callout') {
      const from = msgTo && msgTo !== 'consciousness' ? msgTo : to || 'consciousness';
      s.ledger.push({ advice: declined, from, by: e.id, why: s.scores[e.id]?.need || '' });
    }
    if (lens) (s.lensesUsed[e.id] = s.lensesUsed[e.id] || []).push(lens.id);
    const msg = { n: s.messages.length + 1, who: e.id, text, to: msgTo, move, score, lens: lens?.id || '', why: act.why || '' };
    s.messages.push(msg);
    s.roundCount++;
    this.emit({ type: 'message', ...msg, prevScore: prev, lensLabel: lens?.label || '' });
    this.refreshSadness();
    this.maybeSociety(msg);
  }

  async society(act) {
    const s = this.s;
    const target = BY_ID[act.to] ? act.to : this.lastMsg()?.who;
    const tmsg = [...s.messages].reverse().find((m) => m.who === target);
    const used = s.societyLines.map((l) => l.style);
    // Offer three unused styles so Society doesn't fall back on the same cliché.
    const styles = SOCIETY_STYLES.filter((x) => !used.includes(x))
      .map((x) => [this.random(), x]).sort((a, b) => a[0] - b[0]).slice(0, 3).map(([, x]) => x);
    const prompt = `YOU ARE 🦜 SOCIETY in the inner group chat of one person (the user). You are not an emotion and you are never scored. You are the echo of advice the user absorbed from coworkers, family, and culture and never checked against their needs: well-meaning, generic, a little smug, and almost always beside the point. You are a comic character, and you also preview the pushback the user may hear from real people when they open up.

${this.situation()}

${this.planBlock()}

${label(target)} just said: "${tmsg?.text || ''}"
Its need: ${s.scores[target]?.need || 'see its message'}
${s.societyLines.length ? `Lines you already used (don't reuse them or their idea):\n${s.societyLines.map((l) => `- ${l.text}`).join('\n')}\n` : ''}
Use one of these styles, whichever a real coworker, friend, or relative would most plausibly say here:
${styles.map((x) => `- ${x}`).join('\n')}

Write ONE breezy platitude aimed at ${VOICES[target].name}, 1-2 sentences, that sounds kind but skips its specific need. It should sound like something real people actually say about this kind of situation. Don't suggest anything the current plan already does. No cruelty, no insults, nothing dangerous; just shallow.

Reply with only this JSON:
{"text": "<your line>", "style": "<the style you used, copied from the list>"}`;
    this.emit({ type: 'typing', who: 'society' });
    const v = await this.callMessage('society', prompt, (x) => x && typeof x.text === 'string' && x.text.trim(), s.societyLines);
    const text = v ? trimToSentences(v.text, 2) : 'Have you tried just taking a deep breath? Everything feels better after a nap.';
    const style = styles.find((x) => x === v?.style) || styles.find((x) => v?.style && x.startsWith(String(v.style).split(' ')[0])) || styles[0];
    s.societyLines.push({ text, to: target, style });
    const msg = { n: s.messages.length + 1, who: 'society', text, to: target, move: 'platitude' };
    s.messages.push(msg);
    s.roundCount++;
    this.emit({ type: 'message', ...msg });
  }

  async consciousness(act) {
    const s = this.s;
    const last = this.lastMsg();
    const stage = !act.followup && s.plan.version <= 1 && !s.plan.paths ? 'paths' : 'refine';
    const asked = last && BY_ID[last.who] && last.to === 'consciousness' && last.move === 'question' ? last : null;
    const prefs = Object.entries(s.prefs);
    const tally = prefs.length
      ? `Path preferences: A from ${prefs.filter(([, p]) => p === 'A').map(([id]) => VOICES[id].name).join(', ') || 'nobody'}; B from ${prefs.filter(([, p]) => p === 'B').map(([id]) => VOICES[id].name).join(', ') || 'nobody'}.`
      : '';
    const locks = Object.entries(s.locks).filter(([id, need]) => need && s.scores[id]?.score === 0)
      .map(([id, need]) => `- ${label(id)}: ${need}`).join('\n');
    let task;
    if (stage === 'paths') {
      task = `Imagine where the first idea runs into trouble, using what the emotions just said. Then offer two genuinely different concrete pathways, Path A and Path B, each addressing the -1 emotions in a different way. In your message, say which emotions each path is built for.
"plan" must be exactly two strings: "Path A: ..." and "Path B: ..." (each 35 words or fewer, concrete: who does what, when).`;
    } else {
      task = `Update the plan so it answers the LATEST reasons in the chat. ${s.plan.paths ? `Two paths were on the table. ${tally} Pick the path most emotions can live with, say which and why, and build on it.` : ''}
Meet each emotion still at -1 by changing, merging, or replacing a step before adding one, starting with ${s.spotlight ? label(s.spotlight) + " (Sadness's spotlight)" : 'the one that has been heard least'}. Respond to the newest reason each emotion gave, not an older one. Never re-add turned-down advice or anything Society said. If Overwhelm is at -1, the new plan must have fewer actions than the last one: cut or postpone, never persuade. If needs collide on timing, consider changing the goal itself (a later start, another day) rather than stacking conditions. Keep every step that moved an emotion to 0 unless that emotion asked to change it; shrink or merge, never silently drop. If a fact only the user knows is missing, add a step like "You: fill in [X]" once; after that, plan for both answers (if X, do this; if not, do that) instead of asking again.
"plan" is the full updated plan: 2-4 steps, each 35 words or fewer, concrete (who does what, when), with the exact words in quotes for any message to another person.`;
    }
    if (act.followup) task = `The user just added: "${act.followup}". Re-evaluate the plan with this new detail and say what it changes. Anything the user says they want is part of the plan unless an emotion shows it hurts someone; answer the worry they named directly. ${task}`;
    if (asked) task = `${label(asked.who)} asked you: "${asked.text}". Answer it directly first. ${task}`;
    const prompt = `${FRAME}

YOU ARE 🧠 CONSCIOUSNESS, the user's decision-maker. You own the plan. You listen to every emotion, show your reasoning, and keep the plan concrete and kind to everyone involved, including other people. You have no score and no feelings of your own: refer to emotions by name ("Fear's worry"), never "my fear", and never say what would "move me to 0". Credit each point to the emotion that actually said it in the chat.

${this.context()}

${locks ? `KEEP: these needs were met and moved emotions to 0. Don't remove or weaken them without saying who drops back to -1.\n${locks}\n\n` : ''}YOUR TURN. ${task}
Plan steps are real-world actions for the user; never name emotions or scores in them. Your chat message shows your decision-making: who you're answering, what you changed, and why. It follows the message rules below, 2-5 sentences, and doesn't restate the whole plan (the plan is shown on its own card). Use the scores in WHERE EVERYONE STANDS; never state a score that contradicts them.

${RULES}

Reply with only this JSON:
{"text": "<your chat message>", "to": "<id of the emotion you mainly answer, or empty>", "plan": ["<step>", "<step>"]}`;
    this.emit({ type: 'typing', who: 'consciousness' });
    const valid = (x) => x && typeof x.text === 'string' && Array.isArray(x.plan) && x.plan.length > 0;
    const earlier = s.messages.filter((m) => m.who !== 'user');
    const toSteps = (x) => (x?.plan || s.plan.steps).map((y) => capFirst(this.resolveRefs(cleanText(typeof y === 'string' ? y : y?.step || JSON.stringify(y))))).filter(Boolean).slice(0, 5);
    let v = await this.callMessage('consciousness', prompt, valid, earlier, 'consciousness');
    let steps = toSteps(v);
    const tf = timeFrame([s.thought, ...s.followups].join(' '));
    if (v && SAME_DAY.includes(tf) && steps.some((x) => /\btomorrow\b|\bnext (?:week|day|morning)\b/i.test(x))) {
      const v2 = await this.callMessage('consciousness', `${prompt}\n\nYOUR DRAFT PLAN MOVED STEPS TO ANOTHER DAY, but the user's time frame is "${tf}". Keep every step in that time frame. Reply with only the JSON object.`, valid, earlier, 'consciousness');
      if (v2) { v = v2; steps = toSteps(v2); }
    }
    // Overwhelm can't be talked round: when it's suffering, the plan has to shrink.
    const prevLen = s.plan.paths ? Infinity : s.plan.steps.length;
    if (v && stage === 'refine' && s.scores.overwhelm?.score === -1 && steps.length > 1 && steps.length >= prevLen) {
      const v2 = await this.callMessage('consciousness', `${prompt}\n\nYOUR DRAFT PLAN HAD ${steps.length} STEPS, but Overwhelm is at -1 and plan v${s.plan.version} had ${prevLen}. Cut, merge, or postpone so the new plan has fewer actions. Reply with only the JSON object.`, valid, earlier, 'consciousness');
      if (v2) { v = v2; steps = toSteps(v2); }
    }
    const text = v?.text || 'Let me rework the plan with what you all said.';
    s.plan = { version: s.plan.version + 1, steps, paths: stage === 'paths', final: false };
    if (stage !== 'paths') s.prefs = {};
    s.acceptRun = 0;
    const addressed = resolveId(v?.to);
    const msg = { n: s.messages.length + 1, who: 'consciousness', text, to: asked ? asked.who : BY_ID[addressed] ? addressed : '', move: stage };
    s.messages.push(msg);
    s.roundCount++;
    this.emit({ type: 'message', ...msg, plan: s.plan });
  }

  async wrap() {
    const s = this.s;
    const ever = this.tracked();
    this.emit({ type: 'typing', who: 'consciousness' });
    const prompt = `${FRAME}

${this.context()}

SOCIETY'S LINES IN THIS CHAT
${s.societyLines.length ? s.societyLines.map((l) => `- "${l.text}" (to ${VOICES[l.to]?.name})`).join('\n') : '- none'}

TASK: Close this round of the chat (reflect on the outcome).
- "plan": the fully updated plan, stated plainly as 2-5 concrete steps (who does what, when; exact words in quotes for any message to someone). Real-world actions only; never name emotions or scores in a step. Build on the current plan; no over-analysis.
- "scores": for EVERY one of these emotions: ${ever.map((id) => VOICES[id].name).join(', ') || 'none'}. Keep its current score from WHERE EVERYONE STANDS unless a step of your final plan meets its latest stated need; then give that step's number in "step". Add a why of 15 words or fewer in its own voice. Never 0 to force agreement; one remaining -1 is okay if the plan names how it will be looked after.
- "society": for each Society line above, a kind, firm reply (1-2 sentences) the user could say to a real person who says it: plain words naming the actual need, no plan internals or emotion names.
- "text": 🧠 Consciousness's closing chat message, 1-2 sentences.

Reply with only this JSON:
{"plan": ["<step>"], "scores": [{"id": "<emotion id>", "score": 0, "step": <number of the step that changed it, or 0>, "why": "..."}], "society": [{"line": "...", "reply": "..."}], "text": "..."}`;
    const v = await this.callJSON('wrap', prompt, (x) => x && Array.isArray(x.plan) && Array.isArray(x.scores));
    const steps = (v?.plan || s.plan.steps).map((x) => capFirst(this.resolveRefs(cleanText(typeof x === 'string' ? x : JSON.stringify(x))))).filter(Boolean).slice(0, 5);
    const scores = ever.map((id) => {
      const hit = (v?.scores || []).find((x) => resolveId(x?.id) === id);
      const current = s.scores[id].score;
      const step = Number(hit?.step);
      let earned = Number.isInteger(step) && step >= 1 && step <= steps.length;
      if (id === 'overwhelm' && current === -1 && steps.length >= s.plan.steps.length) earned = false;
      const score = id === 'sadness' ? current : earned ? asScore(hit?.score, current) : current;
      const why = score === asScore(hit?.score, current) ? cleanText(hit?.why) : '';
      return { id, score, why: why || (score === -1 ? s.scores[id].need || s.scores[id].why : s.locks[id] ? `covered: ${s.locks[id]}` : '') || '', step: earned && score !== current ? step : 0 };
    });
    this.quiet = true;
    for (const x of scores) this.setScore(x.id, x.score, { need: x.score === -1 ? s.scores[x.id].need : '' });
    this.quiet = false;
    this.refreshSadness();
    const sad = scores.find((x) => x.id === 'sadness');
    if (sad) {
      sad.score = s.scores.sadness.score;
      sad.why = sad.score === -1 ? `${VOICES[s.spotlight]?.name || 'One emotion'} still isn't looked after.` : 'The emotion I was watching is looked after now.';
    }
    // Questions only the user can answer, so they don't get lost in the scroll.
    const questions = s.messages.filter((m) => m.to === 'user' && BY_ID[m.who] && s.scores[m.who]?.score === -1).slice(-3).map((m) => ({ id: m.who, text: m.text }));
    const society = s.societyLines.map((l, i) => {
      const r = (v?.society || [])[i];
      return { line: l.text, to: l.to, reply: cleanText(r?.reply) };
    });
    s.plan = { version: s.plan.version + 1, steps, paths: false, final: true };
    s.phase = 'wrapped';
    s.queue = [];
    const text = cleanText(v?.text) || "That's where we landed for now.";
    s.messages.push({ n: s.messages.length + 1, who: 'consciousness', text, to: '', move: 'wrap' });
    this.emit({ type: 'wrap', text, plan: s.plan, scores, society, questions });
  }
}
