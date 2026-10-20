# Teffy

A phone-first chat app for the Teffy emotional framework. You tell your 🧠
Consciousness what you're thinking of doing, and your 16 personified emotions
work it out until each one can live with the plan (0) instead of suffering (-1).

It has two tabs.

- **Council chat.** A group chat in which every emotion is its own chatbot.
  After each message the council decides who wants to reply and why: an emotion
  speaks up for its own need, answers someone who addressed it, pushes back when
  advice misses its real problem ("bro, breathing doesn't fix this"), or holds
  back when it would only repeat itself. Every few messages the Consciousness
  folds their asks into the plan and asks a suffering emotion a question. ❤️
  Sadness watches for the emotion whose need is least met. You can jump in at
  any time, speak for any emotion ("My doubt says…"), pause and continue.
- **🦜 Society.** Not an emotion, so it never gets a score: it's the advice
  you've absorbed from coworkers, friends, family and the internet without
  checking whether it meets the need. Right after the openings, and once or
  twice later on a suffering emotion's turn, Society chimes in with that
  well-meaning but beside-the-point advice ("have you tried yoga?", "maybe take
  a nap", "just push through"). It never agrees with the need it's aimed at.
  The emotion calls it out: it quotes what Society said, names the exact detail
  of your situation it skips, and says what's still open.
  Because it previews the pushback you may get when you open up to real people,
  the final plan lists each piece of advice with a kind, firm reply you could
  say back. It never gets a say in the plan, sits out when things are serious,
  and can be turned off in Settings.
- **7 steps.** The original template in one answer: reactions, what you're
  tempted to overlook, the challenges, two pathways, Sadness's pick, and the
  updated plan. Add an objection and the template runs again.

| File | What it is |
| --- | --- |
| `index.html` | The app. Published as a claude.ai artifact, it calls Claude on the viewer's own Claude account, with no API key needed. |
| `engine.js` | The emotions, the reply parser, and the council chat engine: prompts, turn-taking, scoring. Pure logic, so tests run the exact same code. Publish it next to `index.html`. |
| `framework.md` | The framework itself, transcribed from the original "Teffy Bot" prompt. |
| `../.claude/skills/teffy/SKILL.md` | The 7-step template as a Claude Code skill: type `/teffy <your thought>`. |

## Ways to use it

1. **On claude.ai (recommended).** Open the published artifact,
   <https://claude.ai/artifact/75gKkgh8gwtHt6aPwoKVGs> (private to its owner
   until shared). The first time
   you send a thought, Claude asks you to allow the page. Answers count against
   your own Claude plan, like chat messages.
2. **Any chatbot, by copy and paste (7 steps only).** Pick "Copy & paste · any
   chatbot" in Settings (⋯), or open `index.html` from disk. Send copies a full
   prompt; paste it into Claude, ChatGPT or another chatbot, then paste the
   reply back. Council chat needs Claude because it makes many small calls.
3. **In Claude Code.** In this repository, type `/teffy I want to go disc golf
   this morning but…`.

## Choosing the model

Settings (⋯) → "Council runs on":

- **Haiku · low effort** (default): the lightest and cheapest option.
- **Haiku · medium effort**
- **Opus · low effort**
- **Opus · medium effort**

A council chat usually takes 15 to 30 small calls; a 7-step round is one bigger
call. Each 7-step round is labeled with the model that answered it.

## How the council chat works

Each turn, `engine.js` makes up to two calls:

1. **Turn-taking.** One call scores every emotion in the chat against the
   current plan and decides, for each, whether it has something new to say and
   why. Code then picks one speaker: someone the Consciousness or another
   emotion just addressed, suffering voices and Sadness's pick first, never the
   same speaker twice in a row.
2. **The speaker.** A call in that emotion's own persona, with its profile, its
   history in this chat (what it said, what others said to or about it) and the
   transcript, so it doesn't repeat itself and can take the hint when its idea
   was turned down.

**Coming back to an unmet need.** An emotion whose need still isn't met may
raise it again, but never with the same words or reasons. Each time it comes
back through a lens it hasn't used yet:
- why the latest advice misses;
- the concrete moment;
- what it costs;
- what "met" would look like;
- the smallest real version;
- asking a specific emotion for help.

These messages are tagged "↻ coming back to it" in the chat. A comeback only
happens after the plan has changed since that emotion last spoke and still
misses its need. Until then it waits for the Consciousness's answer instead of
repeating itself. Each comeback stays on the emotion's own first request, with
a new specific each time. One helper then gets the floor to address it from its
own angle. After that, the Consciousness answers that latest reason in the plan
itself, never re-offering advice the emotion already turned down. When an
emotion comes round to 0, what it accepted on is recorded and the plan keeps
it. A call-out of Society quotes what Society actually
said and names the exact detail it ignores; "that doesn't help my boundaries"
isn't enough.

A score only moves when something changed for that emotion: the plan, a user
message, or the emotion saying so itself. That keeps emotions from quietly
flipping to 0 without a reason. The chat ends when nobody is suffering after
the plan has been worked on, when nobody has anything new to add, or after 14
emotion messages; then the Consciousness states the final plan.

Your conversations are saved in your browser only (localStorage). Settings →
"Start a new chat" clears the chat.
