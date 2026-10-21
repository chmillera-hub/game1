// Runs Teffy test conversations on a real model through the Claude Code CLI
// (`claude -p`), the same engine the phone page uses.
//
//   node teffy/test/run.mjs                      # every scenario, Haiku 5.5 at low effort
//   node teffy/test/run.mjs --only disc-golf --model claude-sonnet-5-5 --effort medium
//   add --raw to keep every prompt in the JSON record
//
// Writes results/<scenario>.json (events, usage, raw calls) and results/<scenario>.md.

import { spawn } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { Conversation } from '../engine.js';
import { transcriptMarkdown } from './transcript.mjs';
import { checkConversation } from './check.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, all) => (a.startsWith('--') ? [...acc, [a.slice(2), all[i + 1]?.startsWith('--') ? true : all[i + 1] ?? true]] : acc), []),
);
const model = args.model || 'claude-haiku-5-5';
const effort = args.effort || 'low';
const outDir = join(here, args.out || 'results');
const parallel = Number(args.parallel || 4);
const only = args.only ? String(args.only).split(',') : null;
const society = args.society || 'sometimes';
const seed = Number(args.seed || 7);
mkdirSync(outDir, { recursive: true });

// The artifact's `sample` call has no page-controlled system prompt, so the
// tests use a neutral one and put every instruction in the prompt itself.
const SYSTEM = 'You are Claude, answering a request sent by a web page. Follow its instructions exactly.';

function cliAsk(log) {
  return (prompt, { kind }) => new Promise((resolve, reject) => {
    const started = Date.now();
    const child = spawn('claude', [
      '-p', '--model', model, '--effort', effort, '--system-prompt', SYSTEM,
      '--tools', '', '--no-session-persistence', '--output-format', 'json',
    ], { cwd: tmpdir(), stdio: ['pipe', 'pipe', 'pipe'] });
    let out = '';
    let err = '';
    const timer = setTimeout(() => child.kill('SIGKILL'), 180_000);
    child.stdout.on('data', (d) => (out += d));
    child.stderr.on('data', (d) => (err += d));
    child.on('close', (code) => {
      clearTimeout(timer);
      let res;
      try { res = JSON.parse(out); } catch { /* reported below */ }
      if (!res || res.is_error || typeof res.result !== 'string') {
        reject({ code: 'upstream_error', message: `claude exited ${code}: ${(err || out).slice(0, 400)}` });
        return;
      }
      const u = res.usage || {};
      log.push({
        kind, ms: Date.now() - started, prompt, reply: res.result,
        inTokens: (u.input_tokens || 0) + (u.cache_creation_input_tokens || 0) + (u.cache_read_input_tokens || 0),
        outTokens: u.output_tokens || 0,
        thinkingTokens: Object.values(res.modelUsage || {})[0]?.thinkingTokens || 0,
        cost: res.total_cost_usd || 0,
      });
      resolve({ text: res.result });
    });
    child.stdin.end(prompt);
  });
}

function mulberry32(a) {
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

async function runScenario(sc) {
  const calls = [];
  const started = Date.now();
  const convo = new Conversation({
    ask: cliAsk(calls),
    settings: { model, effort, society },
    random: mulberry32(seed + sc.id.length),
    onEvent: (e) => {
      if (e.type === 'message' || e.type === 'opening' || e.type === 'wrap') process.stdout.write('.');
      if (e.type === 'error') console.error(`\n[${sc.id}] error ${e.code}: ${e.message}`);
    },
  });
  const results = [await convo.start(sc.thought)];
  for (const f of sc.followups || []) results.push(await convo.followUp(f));
  const ms = Date.now() - started;
  const data = {
    scenario: sc, model, effort, ms, results,
    usage: {
      calls: calls.length,
      inTokens: calls.reduce((n, c) => n + c.inTokens, 0),
      outTokens: calls.reduce((n, c) => n + c.outTokens, 0),
      thinkingTokens: calls.reduce((n, c) => n + c.thinkingTokens, 0),
      cost: calls.reduce((n, c) => n + c.cost, 0),
    },
    conversation: convo.toJSON(),
    // Prompts are rebuilt from the engine, so keep them out of the record unless asked.
    calls: args.raw ? calls : calls.map(({ prompt, ...c }) => ({ ...c, promptChars: prompt.length })),
  };
  data.checks = checkConversation(data);
  writeFileSync(join(outDir, `${sc.id}.json`), JSON.stringify(data, null, 2));
  writeFileSync(join(outDir, `${sc.id}.md`), transcriptMarkdown(data));
  return data;
}

const scenarios = JSON.parse(readFileSync(join(here, 'scenarios.json'), 'utf8')).filter((s) => !only || only.includes(s.id));
console.log(`Running ${scenarios.length} scenario(s) on ${model} at ${effort} effort, ${parallel} at a time`);
const queue = [...scenarios];
const done = [];
await Promise.all(Array.from({ length: Math.min(parallel, queue.length) }, async () => {
  while (queue.length) {
    const sc = queue.shift();
    const d = await runScenario(sc);
    done.push(d);
    console.log(`\n${sc.id}: ${d.usage.calls} calls, ${(d.ms / 1000).toFixed(0)}s, $${d.usage.cost.toFixed(4)}, ${d.checks.summary}`);
  }
}));
const summary = done.map((d) => ({ id: d.scenario.id, calls: d.usage.calls, seconds: Math.round(d.ms / 1000), cost: +d.usage.cost.toFixed(4), ...d.checks.metrics, flags: d.checks.flags }));
writeFileSync(join(outDir, 'summary.json'), JSON.stringify({ model, effort, society, summary }, null, 2));
console.log(`\nWrote ${outDir}`);
