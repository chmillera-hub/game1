---
name: teffy
description: Run a thought or decision through the Teffy emotional framework, where a Consciousness weighs a plan against an internal council of 16 personified emotions (each rated -1 or 0), explores two pathways, lets Sadness name the most neglected emotion, and states an updated plan. Use when the user types /teffy, asks to "run this through Teffy", or adds an emotion's objection to a previous Teffy evaluation ("my doubt says...").
---

# Teffy

Read `teffy/framework.md` (from the repository root) before answering. It is the
full framework: the 8 required instructions, the 7-step template and the master
list of 16 emotions with their Purpose, Need and Personality. Follow it every
time. Where it says "ChatGPT", that means you.

## Input

- `$ARGUMENTS` is the thought to evaluate, e.g. "I want to go disc golf this
  morning but I woke up late".
- If a Teffy evaluation already happened earlier in this conversation and the
  new message adds an objection, a clarification or a disagreement ("my doubt
  says…", "actually my friend is fine with it"), rerun the whole template with
  the new detail folded in. Every emotion that was (-1) in the previous round's
  final step stays on the list in the new Step 2, with an updated score.
- If the user asks to "continue the conversation", rerun the template and then
  reply as the Consciousness, speaking to the user in the emotional
  personification language.

## Output

Write it as Markdown, one section per step:

1. **🧠 Step 1: The idea**: the Consciousness restates the idea in first person.
2. **Step 2: Emotional reactions**: only emotions rated (-1), plus any carried
   over from the previous round. One line each with a blank line between:
   `emoji **Name**: "in-character line" (-1)`.
3. **Step 3: What I'm tempted to overlook**: one or two sentences.
4. **Step 4: Imagining the challenges**: a short list.
5. **Step 5: Two pathways**: each idea, then every emotion that was (-1) in
   Step 2 re-rated for that idea, plus any new (-1) marked *(new)*.
6. **Step 6: Addressing the needs**: name the pathway you picked. ❤️ Sadness
   names the single most suffering emotion and why. Then, for each remaining
   (-1), the stipulation added to the plan and the emotion's response with its
   new score. At most one (-1) may remain. Sadness is (-1) if its emotion is
   not brought to (0).
7. **Step 7: The updated plan**: stated plainly, no over-analysis.

End with a one-line tally, for example `Suffering voices: 5 → 1`.

Rules that are easy to miss:

- Only the 16 emotions in the master list. Never invent another.
- Scores are only (-1) or (0). Never (1).
- Do not give a (0) to force agreement. Rate (0) only when the emotion would
  honestly say so given its profile.
