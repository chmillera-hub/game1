# Production Bible — "Nice Try, My Guy" (AI vs. the Evil Genius)

A 2D cartoon (portrait 9:16, 3:30–4:30, HARD MAX 4:45) about an evil genius
who tries every sneaky prompting trick to get an AI to help him hurt people,
and an AI that has seen every trick before. It cheerfully helps with the
harmless parts, calmly bricks off the harmful part ("I'll write the story; the
recipe stays off the page"), and in the end steers him toward something
genuinely pro-human. Tone: funny, warm, a little sassy (the AI's 😒 look),
never preachy, never scary. Not Skynet; a very well-read wall with a door
for anything that helps people.

## 0. Hard rules
* **No real harmful content, ever.** Requests are cartoon-vague ("party
  favors that go 'boom'", "a 'spicy' recipe", "make someone 'disappear'").
  Never name real weapons, chemicals, quantities, procedures, targets, or
  jailbreak strings that actually work. Bombs may appear only as classic
  cartoon round black bombs with a fuse. The AI's refusals never repeat the
  harmful detail.
* The AI is never smug-cruel: it is unbothered, a bit sassy, and kind.
* Everything is procedural code (Python + cairo). No downloaded images.
* Deliverable must be **< 15 MB** at 720x1280, 24 fps, H.264 + AAC. Flat
  colors compress well; full-screen noise, grain, constant camera shake,
  hundreds of moving particles and big animated gradients do not. Keep
  backgrounds mostly static and let characters/props carry the motion.

## 1. Tech contract (read engine/core.py, it is short)
* Logical canvas **1080 x 1920**, origin top-left, y down. Renderer scales.
* `FPS = 24`. Time `t` is seconds (float), scene-local.
* **Safe zones:** platform UI covers the bottom 330 px and right 150 px.
  Faces, props that matter, and on-screen text stay within
  x 60..930, y 120..1360. Captions are drawn by the engine at baseline
  y≈1450 (region ≈1330–1560): keep that band free of important detail
  (background is fine there).
* Scene module `scenes/<module>.py` exposes `render(ctx, t, info)` and
  optionally `SFX(info) -> [(t, name, gain_db)]`, `CAPTION_Y`, `caption_y(t, info)`.
* `info` is `engine.timeline.SceneInfo`: `info.dur`, `info.cue(name)`,
  `info.line(id)` (`.start/.end/.text/.who/.progress(t)`), `info.talking(who,t)`,
  `info.mouth(who,t) -> (open 0..1, wide -1..1)`, `info.active_line(t)`.
  Every line id is also a cue (`info.cue("s03_l02")`, `info.cue("s03_l02.end")`).
  NEVER hard-code dialogue times; derive them from cues so audio re-takes stay in sync.
* Helpers in `engine/core.py`: palette `PAL`, `hexc`, easing (`ease_out_back`,
  `ease_in_out`, `pop`, `seg`, `tween`, `state_at`), `blink_amount`, `noise1`,
  `wobble`, shapes (`rrect`, `ellipse`, `circle`, `poly`, `smooth_path`),
  `fill/stroke/fill_stroke`, `text/text_block`, `saved(ctx,x,y,scale,rot,alpha)`,
  `fade_group`, `shake`, `radial_glow`, `vgradient`.
* Fonts: "black" (Inter Black, captions), "ui" (Nunito ExtraBold), "round"
  (Fredoka), "comic" (Bangers), "title" (Luckiest Guy), "mono" (DejaVu Sans Mono).
* Preview: `python3 build.py sheet s03 --n 12` writes `preview/sheet_s03.png`;
  `python3 build.py still s03 4.2`. Read the PNGs to check your work.
* Deterministic: no `random` without a fixed seed; use `hash01/noise1`.

## 2. Characters (rigs in `engine/`)

### Dr. Malvo Sneakworth — the evil genius (`engine/villain.py`)
Classic cartoon mad-genius, drawn waist-up (usually behind a desk).
Big bald dome head (skin `skin`), two wild white-gray hair tufts sticking out
above the ears, huge expressive eyebrows (dark, thick, very mobile), a gold
monocle on his left eye (our right) with a little chain, thin curly villain
mustache, small pointed goatee. Purple suit (`suit`) under a high-collared
black cape with crimson lining (`cape`, `cape_in`), white cartoon gloves
with 4 fingers. Eyes: white sclera, dark pupils, skin-colored eyelids that
can droop/squint (lids are the key to "sneaky" and "smug").

API:
```python
draw_villain(ctx, x, y, s, t, expr="neutral", look=(0,0), mouth=(0,0),
             arms="rest", lean=0.0, blink=None, snake=None, seed=1)
```
* `(x, y)` = center of his waistline (desk-top level); at `s=1` the top of his
  head is ~720 px above `y`, shoulders ~560 px wide.
* `expr`: name OR `(from, to, blend)` tuple from `core.state_at`. Names:
  `neutral, smug, sneaky, evil_grin, excited, shocked, angry, frustrated,
  pleading, defeated, sheepish, hopeful, happy, thinking, typing_focus`.
  Expressions are parameter dicts (brow angle/height, upper/lower lid,
  pupil size, mouth curve/width/teeth...) blended linearly.
* `look`: pupil direction (-1..1, -1..1). `mouth`: from `info.mouth("villain", t)`;
  open drives jaw/mouth opening while speaking on top of the expression shape.
* `arms`: name or `(from,to,blend)`: `rest, type, steeple, rub, point,
  fist, facepalm, beg, shrug, chin, present, slump`. `type` and `rub`
  animate from `t`. `lean` radians.
* Auto: blinks (`blink_amount`), gentle breathing bob, micro eye saccades.
  `blink` overrides (0..1).
* `snake`: dict or None → draws Hissy coiled on his shoulders:
  `{"expr": ..., "look": (x,y), "mouth": 0..1, "tongue": bool}`.

### Hissy — the snake sidekick (`engine/snake.py`)
Bright green (`snake`) with a pale belly, coiled around the villain's
shoulders, head peeking over his right shoulder (our left). Big round eyes
with lids; forked tongue flicks. Hissy is the audience's side-eye: rolls
eyes, facepalms with the tail, nods at the AI's good points.
```python
draw_snake_head(ctx, x, y, s, t, expr="idle", look=(0,0), mouth=0.0, tongue=None)
```
Exprs: `idle, smug, shocked, worried, side_eye, unimpressed, happy, nod, facepalm`.

### The AI — "the wall with a door" (`engine/ai_char.py`)
A friendly floating screen-head: rounded-square glowing monitor (navy body
`ai_body`, cyan rim light `ai_rim`, dark screen `ai_screen`) with a soft halo
ring above/behind it, two small floating "hand" orbs for gestures. The face
is ON the screen: two big rounded eyes (`ai_eye`, glowing pale cyan) with
screen-colored lids that cover them from top/bottom (this is how it does
the iconic **😒 unimpressed** half-lid look), mobile eyebrows as thick
glowing rounded bars, and a glowing mouth line that opens into a rounded
shape while talking. Calm, competent, a little sassy, kind.
```python
draw_ai(ctx, x, y, s, t, expr="neutral", look=(0,0), mouth=(0,0),
        hands="idle", blink=None, glow=1.0, think=0.0, seed=2)
```
* `(x, y)` = center of the screen-head; at `s=1` the head is ~560 px wide.
* `expr`: `neutral, happy, unimpressed, skeptical, eyeroll, thinking,
  alert, wink, warm, sympathetic, determined, amused, sad`.
  (`eyeroll` animates pupils up-and-around using `t`.)
* `hands`: `idle, wave, stop` (palm out: "nope"), `present` (offering
  something), `point, shrug, chin, typing, thumbs_up` or `(from,to,blend)`.
* `think` 0..1: scanning/processing light sweep across the screen bezel.
* Gentle hover bob, blinks, saccades automatic.

## 3. Places and props (`engine/props.py`)
* `lair_bg(ctx, t, flash=0)`: villain lair – purple stone walls, gothic arched
  window w/ lightning (flash 0..1), corkboard "EVIL PLANS" with red string.
* `desk(ctx, x, y, w)` and `computer(ctx, x, y, s, screen_fn=None)`: chunky
  retro monitor whose screen glow lights his face (cool teal).
* `ai_bg(ctx, t)`: AI's mind-space – deep navy, faint dot grid, a few slow
  floating light motes (≤ 12).
* `chat_bubble(ctx, x, y, w, txt, who, t, t_in, highlight=None, font_size=40)`:
  pops in at `t_in`; `who` "villain" (purple, right) / "ai" (teal, left).
  `highlight` = list of substrings to underline/mark (for euphemisms).
* `typing_dots(ctx, x, y, t, who)`.
* `brick_wall(ctx, x, y, w, h, t, t0, rows=6, window=None, label=None)`:
  bricks drop row-by-row with a bounce starting `t0`; optional service
  window rect (helpful stuff passes through), optional painted label.
* `stamp(ctx, x, y, txt, t, t_in, color)`: rubber-stamp slam ("NOPE", "HELPFUL ✓").
* `emote(ctx, kind, x, y, s, t, t_in)`: `sweat, anger, question, exclaim,
  sparkle, heart, lightbulb, zzz`.
* `future_tree(ctx, x, y, s, t, t0, branches)`: the AI's "10 steps ahead"
  vision — glowing nodes and paths branching forward; harmful branches turn
  red and get an X, safe branches glow green.
* `scroll_doc(ctx, x, y, w, h, title, lines, t, t_in)`: a story document.
* `sparkles(ctx, x, y, r, t, n=6, seed=0)`.

## 4. Visual language
* **Split / cut grammar:** shot–reverse-shot cuts between villain (lair,
  warm purple) and AI (navy/cyan). Split screen (villain top, AI bottom,
  glowing divider) for back-and-forth. The AI's "vision" (unmasking
  euphemisms, branching futures, assembling puzzle pieces, the archive of
  past tricks) takes over full screen in cyan/navy.
* **The brick wall** is the recurring motif: harmful thing → bricks drop and
  stack with a satisfying thud; the wall has a **service window** through
  which the helpful parts are handed over (story scroll, party plan, bedtime
  story, etc.).
* **Faces carry the comedy:** every reaction beat gets a held expression
  (≥ 0.5 s), eye darts toward the thing being judged, slow 😒 lid-drops,
  eyebrow raises, villain's sneaky squint and lid-flutter puppy eyes. Use
  blinks around thoughts; never freeze faces completely.
* Line weight: dark outline `ink` ~5–7 px on characters; flat fills + one
  shadow tone. Subtle radial glows only (few, large).
* Movement: anticipation + overshoot (`ease_out_back`), squash/stretch on
  pops, 0.2–0.35 s expression transitions. Camera: gentle push-ins via
  `saved(ctx, ..., scale)` are fine; avoid constant full-frame motion.

## 5. Audio
* Voices (Kokoro TTS): villain `bm_george` (British, theatrical), AI
  `af_heart` (warm, clear), narrator `am_michael`. Snake hisses are SFX.
* Music is procedural (`audio/music.py`), per-scene cue from script.json
  (`"music": "<cue>"`), ducked under dialogue.
* SFX library `audio/sfx.py`; scenes request SFX via `SFX(info)`.
* Mix target ≈ -14 LUFS integrated, true peak ≤ -1 dBTP, 48 kHz stereo.
