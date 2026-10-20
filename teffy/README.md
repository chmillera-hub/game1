# Teffy

A chat app for the Teffy emotional framework. You tell your 🧠 Consciousness
what you're thinking of doing, and a council of 16 personified emotions reacts
(-1 suffering, 0 at peace). The Consciousness weighs two pathways, Sadness names
the emotion that needs the most care, and you get an updated plan. Add an
objection from any emotion ("my doubt says…") and the whole template runs again.

| File | What it is |
| --- | --- |
| `index.html` | The app. Published as a claude.ai artifact, it calls Claude on the viewer's own Claude account, with no API key needed. |
| `framework.md` | The framework itself, transcribed from the original "Teffy Bot" prompt. |
| `../.claude/skills/teffy/SKILL.md` | The same framework as a Claude Code skill: type `/teffy <your thought>`. |

## Three ways to use it

1. **On claude.ai (recommended).** Open the published artifact. The first time
   you send a thought, Claude asks you to allow the page. Answers count against
   your own Claude plan, the same as a chat message.
2. **Any chatbot, by copy and paste.** Pick "Copy & paste · any chatbot" in the
   "Council runs on" menu, or open `index.html` from disk. Send copies a full
   prompt to your clipboard. Paste it into Claude, ChatGPT or another chatbot,
   then paste its reply back into the page.
3. **In Claude Code.** In this repository, type `/teffy I want to go disc golf
   this morning but…`.

## Choosing the model

The "Council runs on" menu picks who answers:

- **Haiku · low effort** (default): the lightest and cheapest option.
- **Haiku · medium effort**
- **Opus · low effort**
- **Opus · medium effort**

Each round is labeled with the model that answered it, so you can compare rounds
side by side. If your plan can't use the model you picked, Claude falls back to
the nearest setting and the round says so.

## How a reply is shaped

The page asks Claude to answer in JSON Lines, one object per line:
`idea`, `react`, `overlook`, `challenge`, `path`, `pathReact`, `choose`,
`sadness`, `care`, `plan`, `voice`. The page draws each line as it arrives. The
parser also accepts code fences, prose around the objects, and pretty-printed
JSON, which helps when the reply is pasted from another chatbot.

Your conversation is saved in your browser only (localStorage). "New thought"
clears it.
