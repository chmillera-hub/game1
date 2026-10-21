// Renders a recorded Teffy conversation as Markdown for reading and judging.
import { VOICES, MOVE_LABELS } from '../engine.js';

const name = (id) => (VOICES[id] ? `${VOICES[id].emoji} ${VOICES[id].name}` : id || '?');

export function transcriptMarkdown(data) {
  const { scenario, model, effort, usage, ms } = data;
  const out = [
    `# ${scenario.id}`,
    '',
    `Model: ${model} at ${effort} effort · ${usage.calls} calls · ${(ms / 1000).toFixed(0)} s · ${usage.inTokens} input tokens, ${usage.outTokens} output tokens · $${usage.cost.toFixed(4)}`,
    '',
  ];
  for (const e of data.conversation.events) {
    switch (e.type) {
      case 'user':
        out.push(`**🙋 You:** ${e.text}`, '');
        break;
      case 'opening':
        out.push(`**🧠 Consciousness** (opening): ${e.text}`, '', `> Plan v1: ${e.plan.steps[0]}`, '');
        out.push(`First reactions (-1): ${e.minus.map((m) => `${name(m.id)} "${m.why}"`).join(' · ') || 'none'}`);
        out.push(`Sadness's spotlight: ${name(e.spotlight)}`, '');
        break;
      case 'bids': {
        const parts = e.bids.map((b) => `${b.act === 'reply' ? '✋' : '🤐'} ${VOICES[b.id].name} ${b.score} ${b.move}${b.to ? `→${VOICES[b.to]?.name || b.to}` : ''}${b.prefers ? ` [${b.prefers}]` : ''}: ${b.why}`);
        out.push(`<sub>deciding: ${parts.join(' · ')} ⇒ **${e.pick ? VOICES[e.pick].name : 'nobody'}**</sub>`, '');
        break;
      }
      case 'message': {
        const tag = [MOVE_LABELS[e.move] || e.move, e.to ? `→ ${name(e.to)}` : '', e.lensLabel ? `angle: ${e.lensLabel}` : '',
          e.score !== undefined && VOICES[e.who] && e.who !== 'consciousness' && e.who !== 'society' ? `score ${e.prevScore ?? '·'}→${e.score}` : ''].filter(Boolean).join(' · ');
        out.push(`**${name(e.who)}** _(${tag})_: ${e.text}`, '');
        if (e.plan) {
          out.push(`> Plan v${e.plan.version}${e.plan.paths ? ' (two paths)' : ''}:`);
          for (const s of e.plan.steps) out.push(`> - ${s}`);
          out.push('');
        }
        break;
      }
      case 'score':
        out.push(`_${name(e.id)} ${e.from} → ${e.to}_`, '');
        break;
      case 'spotlight':
        out.push(`_Sadness's spotlight moves to ${name(e.id)}_`, '');
        break;
      case 'wrap':
        out.push(`**🧠 Consciousness** (wrap-up): ${e.text}`, '', '**Final plan**');
        for (const s of e.plan.steps) out.push(`- ${s}`);
        out.push('', '**Where everyone landed**');
        for (const s of e.scores) out.push(`- ${name(s.id)} ${s.score}${s.step ? ` (changed at wrap by step ${s.step})` : ''}: ${s.why}`);
        if (e.questions?.length) {
          out.push('', '**Questions for you**');
          for (const q of e.questions) out.push(`- ${name(q.id)}: ${q.text}`);
        }
        if (e.society.length) {
          out.push('', '**If people say this…**');
          for (const s of e.society) out.push(`- 🦜 "${s.line}" → "${s.reply}"`);
        }
        out.push('');
        break;
      case 'error':
        out.push(`**ERROR ${e.code}:** ${e.message}`, '');
        break;
      default:
    }
  }
  const c = data.checks;
  if (c) {
    out.push('---', '', `**Automatic checks:** ${c.summary}`);
    for (const f of c.flags) out.push(`- ${f}`);
  }
  return out.join('\n');
}
