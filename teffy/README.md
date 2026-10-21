# Teffy: your inner council, as a group chat

Teffy turns the Teffy emotional framework into a group chat you can watch. You type a thought or a plan. Your 🧠 Consciousness puts it to 16 personified emotions. Each emotion is its own chatbot, scored −1 (its need isn't met, so it suffers) or 0 (it can live with the plan, even grudgingly). They negotiate until every emotion reaches 0. 🦜 Society butts in with well-meaning, beside-the-point advice and gets called out.

Built for a phone (Pixel-sized screens first). It runs on your own Claude account, through the Claude app or claude.ai.

## How a conversation works

1. **Opening.** The Consciousness restates your first idea, a little too confidently (Step 1 and Step 3 of the framework). The council's first reactions list every emotion at −1 (Step 2). ❤️ Sadness picks the emotion heard least.
2. **Turn-taking.** After each message, the emotions with a stake bid to speak. Each one either wants in (✋) or holds back (🤐) and says why. Tap "why?" under a message to see the bids. The engine gives the floor to:
   - whoever was addressed;
   - whoever was pushed back on;
   - whoever has waited longest.

   Nobody speaks twice in a row.
3. **Moves.** An emotion can:
   - state its need;
   - push back on advice that misses it;
   - answer a question;
   - offer help from its own angle;
   - ask a question, saying why it asks;
   - accept a changed plan;
   - come back to an unmet need.

   A comeback must use a new angle: the exact moment, why it misses, the cost, what "met" looks like, the smallest next step, or a picture.
4. **Consciousness.** After about three emotion messages, the Consciousness revises the plan. Its first revision imagines the challenges and offers Path A and Path B (Steps 4–5). Later revisions pick a path and change or cut steps to meet the latest reasons (Step 6). If 😵‍💫 Overwhelm is at −1, the plan must get smaller.
5. **Society.** After an emotion states a specific need, 🦜 Society may chime in with a platitude ("have you tried yoga?"). Society is never scored and never enters the plan. The emotion it talked past, or another suffering emotion, calls it out with specifics.
6. **Wrap-up.** The round ends when everyone reaches 0, nobody has anything new to say, or the round hits its message limit. The wrap-up shows:
   - the final plan, stated plainly (Step 7);
   - where each emotion landed;
   - questions only you can answer;
   - "If people say this…": each Society line with a kind, firm reply you could give a real person.
7. **Follow-ups.** Type more ("but my doubt says…") and the council re-evaluates with the new detail.

### Message rules every voice follows

- One paragraph that fits a chat bubble. Usually 2–4 sentences, never more than 6, no line breaks.
- Radically non-violent and pro-human. No insults, labels, or "tell them they're a bad person".
- Hyper-precise and actionable: the specific barrier, who does what and when, and the actual words for any message to someone.
- Humor and slang are fine only if the same message says what it means and what it wants the Consciousness to do.
- A question says why it's asked and what answer would settle it. No dithering.
- No repeating or copying. Each voice speaks only as itself and argues from its own need.

The engine also checks each message in code before showing it: length, harsh words, near-copies of earlier messages, re-quoted scripts, and a voice speaking as another emotion. A failing message gets one rewrite.

## Model and cost

The default is **Claude Haiku 5.5 at low effort**, the lightest model on Claude. You can switch to Sonnet 5.5 or Opus 5.5, and to medium or high effort, in Settings. A conversation makes about 30–35 small calls. In the Haiku-low test runs below, one full conversation cost about **$0.06–0.07** at API prices. In the app, these calls count against your own Claude plan's usage, not an API bill.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The phone app. It talks to Claude through the artifact runtime's `sample` capability, on the viewer's own account. |
| `engine.js` | The conversation engine: the 16 personas from the framework PDF, every prompt, turn-taking, Society, the scoring rules, and the message checks. It has no DOM code, so the page and the tests share it. |
| `test/run.mjs` | Runs the test scenarios against a real model through the Claude Code CLI (`claude -p`). |
| `test/scenarios.json` | The test thoughts (overwhelm at work, disc golf, a coworker taking credit, and more). |
| `test/check.mjs` | Automatic checks: bubble length, repetition, turn-taking, Society call-outs, question framing. |
| `test/results/`, `test/results-medium/` | Recorded transcripts (`.md`) and data (`.json`) from the final runs at low and medium effort. `test/results-round1/` is the first run, before the fixes. |
| `test/embed-example.mjs`, `test/example/` | Copies a recorded conversation into `index.html` as the example new visitors see, and the recording it uses. |

## Test results

Eight test thoughts ran through the full engine on real models. Opus agents at medium effort judged the transcripts against the requirements above, and their findings drove four rounds of prompt and engine fixes.

| Run | Calls per conversation | Cost per conversation | Avg sentences per message | Worst repetition overlap | Society lines called out | Conversations with Society |
| --- | --- | --- | --- | --- | --- | --- |
| Round 1, Haiku 5.5 low (`results-round1/`) | 32 | $0.065 | 3.2 (max 6) | 0.38 | 16 of 16 | 8 of 8 |
| Final, Haiku 5.5 low (`results/`) | 35 | $0.070 | 3.1 (max 6) | 0.28 | 12 of 12 | 8 of 8 |
| Final, Haiku 5.5 medium (`results-medium/`) | 33 | $0.078 | 3.0 (max 5) | 0.37 | 15 of 15 | 8 of 8 |

The final low and medium runs use the same engine. The disc-golf scenario includes a follow-up message, so it makes about 50 calls; the others make 27–37.

"Worst repetition overlap" is the highest share of word triples any message shares with an earlier one. Emotions left at −1 aren't failures: an honest −1 beats a forced 0.

### Is Haiku at low effort good enough?

Opus judges compared the same conversations at Haiku 5.5 low and medium effort. Their scores are 1–10 judgments of one conversation per scenario, so gaps under a point are noise.

| Scenario | Low | Medium |
| --- | --- | --- |
| Disc golf, with a follow-up | 5.5 | 7.0 |
| Sister's comments | 6.5 | 7.5 |
| Exam all-nighter | 7.0 | 7.5 |
| Quit and travel | 5.5 | 8.0 |
| **Average** | **6.1** | **7.5** |

**Where low effort holds up.** Every message comes out short, kind and concrete, with the actual words to send. Turn-taking, holding back with reasons, and Society's call-outs work just as well as at medium. Messages are slightly shorter at low effort, and the code guards keep the user's time frame and make Society appear in every conversation.

**Where medium is better.** Medium keeps a longer conversation coherent:
- comebacks bring genuinely new angles, where low tends to loop on one ask;
- each voice argues its own need, and the Consciousness credits the right emotion;
- the plan shrinks for Overwhelm and doesn't contradict its own message;
- follow-ups get built into the plan.

**Cost.** Medium used about 2.3× the output tokens. Because the prompts (input tokens) dominate, the whole conversation cost only about 15% more, and it took about a third longer.

Low effort stays the default because it uses the least. If conversations feel loopy or shallow, switch Effort to Medium in Settings; based on these tests, that's the single biggest quality gain for the money.

`example/` holds the conversation the app opens with. The recorded transcripts in `results/` predate one fix: plan steps that say "send Embarrassment's text" now get the actual quoted words only when that emotion wrote a message to someone. In the recorded quit-and-travel run, a quoted plan suggestion was pasted into a text by mistake.

## Running the tests

These commands need the Claude Code CLI, signed in.

```sh
node teffy/test/run.mjs                                   # all scenarios, Haiku 5.5 at low effort
node teffy/test/run.mjs --only disc-golf --effort medium  # one scenario at another effort
node teffy/test/run.mjs --model claude-sonnet-5-5         # compare against a stronger model
```

Each run writes a readable transcript per scenario, including who bid to speak and why, score changes, and plan versions. It also writes `summary.json` with the automatic-check metrics.
