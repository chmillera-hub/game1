// Automatic checks on a recorded Teffy conversation: bubble length,
// repetition, turn-taking, Society call-outs, question framing.
import { sentences, overlap, VOICES } from '../engine.js';

const REASON = /\b(because|so (?:that|i|we|you)|since|which would|that would|would settle|i'm asking|asking because|to know whether|if (?:yes|no|so))\b/i;
const HARSH = /\b(idiot|stupid|moron|jerk|asshole|loser|bad person|shut up|worthless|incompetent|selfish)\b/i;

export function checkConversation(data) {
  const events = data.conversation.events;
  const msgs = events.filter((e) => e.type === 'message' || e.type === 'opening');
  const chat = msgs.filter((m) => m.type === 'message');
  const flags = [];

  const sentenceCounts = chat.map((m) => sentences(m.text).length);
  const over6 = chat.filter((m, i) => sentenceCounts[i] > 6);
  const wordy = chat.filter((m) => m.text.split(/\s+/).length > 110);
  over6.forEach((m) => flags.push(`over 6 sentences: [${m.n}] ${m.who}`));
  wordy.forEach((m) => flags.push(`over 110 words: [${m.n}] ${m.who}`));

  let backToBack = 0;
  for (let i = 1; i < chat.length; i++) {
    if (chat[i].who === chat[i - 1].who) {
      backToBack++;
      flags.push(`same voice twice in a row: [${chat[i].n}] ${chat[i].who}`);
    }
  }

  let maxOverlap = 0;
  const repeats = [];
  for (let i = 0; i < chat.length; i++) {
    for (let j = 0; j < i; j++) {
      const o = overlap(chat[i].text, chat[j].text);
      if (o > maxOverlap) maxOverlap = o;
      if (o > 0.3) repeats.push(`[${chat[i].n}] ${chat[i].who} echoes [${chat[j].n}] ${chat[j].who} (${o.toFixed(2)})`);
    }
  }
  flags.push(...repeats);

  const societyLines = chat.filter((m) => m.who === 'society');
  let calledOut = 0;
  for (const s of societyLines) {
    const next = chat.find((m) => m.n > s.n && m.who !== 'society');
    if (next?.move === 'callout') calledOut++;
    else flags.push(`Society line [${s.n}] not called out next`);
  }

  const unquoted = (t) => t.replace(/["“][^"“”]*["”]/g, ' ').replace(/(^|[\s:(])['‘][^'’]{3,}['’](?=[\s.,;!?)]|$)/g, ' ');
  const questions = chat.filter((m) => VOICES[m.who] && m.who !== 'society' && unquoted(m.text).includes('?'));
  const bareQuestions = questions.filter((m) => !REASON.test(m.text));
  bareQuestions.forEach((m) => flags.push(`question without a stated reason? [${m.n}] ${m.who}`));

  const harsh = chat.filter((m) => HARSH.test(m.text));
  harsh.forEach((m) => flags.push(`harsh word: [${m.n}] ${m.who}`));

  const bids = events.filter((e) => e.type === 'bids').flatMap((e) => e.bids);
  const holdRate = bids.length ? bids.filter((b) => b.act === 'hold').length / bids.length : 0;

  const speakers = {};
  for (const m of chat) speakers[m.who] = (speakers[m.who] || 0) + 1;

  const wraps = events.filter((e) => e.type === 'wrap');
  const lastWrap = wraps[wraps.length - 1];
  const finalMinus = lastWrap ? lastWrap.scores.filter((s) => s.score === -1).map((s) => s.id) : null;
  const errors = events.filter((e) => e.type === 'error');
  errors.forEach((e) => flags.push(`error ${e.code}: ${e.message.slice(0, 120)}`));
  if (!lastWrap) flags.push('never reached a wrap-up');

  const metrics = {
    messages: chat.length,
    voices: Object.keys(speakers).length,
    maxSentences: Math.max(0, ...sentenceCounts),
    avgSentences: +(sentenceCounts.reduce((a, b) => a + b, 0) / (sentenceCounts.length || 1)).toFixed(1),
    over6: over6.length,
    backToBack,
    maxOverlap: +maxOverlap.toFixed(2),
    societyLines: societyLines.length,
    societyCalledOut: calledOut,
    questions: questions.length,
    bareQuestions: bareQuestions.length,
    holdRate: +holdRate.toFixed(2),
    finalMinus,
    errors: errors.length,
  };
  const summary = `${metrics.messages} msgs, ${metrics.voices} voices, avg ${metrics.avgSentences} sentences (max ${metrics.maxSentences}), max overlap ${metrics.maxOverlap}, Society ${calledOut}/${societyLines.length} called out, hold rate ${metrics.holdRate}, final -1: ${finalMinus ? finalMinus.join(', ') || 'none' : 'n/a'}${flags.length ? `, ${flags.length} flag(s)` : ''}`;
  return { metrics, flags, summary, speakers };
}
