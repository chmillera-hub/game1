// Embeds a recorded test conversation into index.html as the example that
// greets first-time visitors:  node teffy/test/embed-example.mjs teffy/test/example/weekend-overwhelm.json
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { MODELS } from '../engine.js';

const here = dirname(fileURLToPath(import.meta.url));
const data = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const { state, events } = data.conversation;
const example = {
  model: MODELS.find((m) => m.id === data.model)?.label || data.model,
  effort: data.effort,
  events,
  state: { thought: state.thought, scores: state.scores, spotlight: state.spotlight, plan: state.plan, ledger: state.ledger, societyLines: state.societyLines },
};
const page = join(here, '..', 'index.html');
const html = readFileSync(page, 'utf8');
const json = JSON.stringify(example).replace(/</g, '\\u003c');
const next = html.replace(/(<script type="application\/json" id="example-data">)[\s\S]*?(<\/script>)/, (_, a, b) => `${a}${json}${b}`);
if (next === html) throw new Error('example-data tag not found');
writeFileSync(page, next);
console.log(`Embedded ${data.scenario.id} (${events.length} events, ${(json.length / 1024).toFixed(0)} KB)`);
