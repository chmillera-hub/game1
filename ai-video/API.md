# Engine API notes (from the rig / props / audio builders)


## AI rig

The AI character rig is done: `/home/user/game1/ai-video/engine/ai_char.py`. It draws in about 6.2 ms at s=1 and 720x1280, under the 8 ms target. I did 4 rounds of render, look and fix, and checked every sheet by eye.

**Signature** (the SPEC §2 signature, plus 4 optional keyword args at the end):
```python
draw_ai(ctx, x, y, s, t, expr="neutral", look=(0,0), mouth=(0,0), hands="idle",
        blink=None, glow=1.0, think=0.0, seed=2,
        roll0=None, aura=1.0, shake=0.0, nod=0.0) -> dict of anchors
```
- **expr**: a name, a `(from, to, blend)` tuple from `core.state_at`, or a dict of parameters. Blending between expressions is smooth.
  - Names (`EXPRS`): neutral, happy, unimpressed, skeptical, eyeroll, thinking, alert, wink, warm, sympathetic, determined, amused, sad.
  - `eyeroll` loops every 1.5 s using `t`. Pass `roll0=<cue time>` to play it once and settle into the 😒 look. I recommend `roll0` for scenes, because otherwise the start of the loop depends on `t`.
- **hands**: a name or a `(from, to, blend)` tuple (`HAND_POSES`): idle, wave, stop, stop_both, present, present_l, present_both, point, point_l, point_up, shrug, chin, typing, thumbs_up, thumbs_both, fists.
  - Hands move on an arc between poses.
  - "L" and "R" mean the side of the screen, not the character's side. Single-hand gestures use R, except `stop`, which uses L. The `_l` variants use the other hand.
  - When a hand turns over mid-move it narrows for about 2 frames, like a side view of the hand.
- **mouth**: `(open, wide)` lip-sync is layered on top of each expression's mouth, so the AI visibly talks in every expression.
- **look**: if the look goes against an expression's built-in side-glance, the whole face mirrors smoothly. So `unimpressed` with `look=(-1,0)` gives a proper left side-eye instead of centred pupils.
- **think**: 0..1 adds a light sweeping round the bezel, data ticks, and a gold status light.
- **Extras**: `aura=0` turns off the soft back-glow (use it over busy backgrounds). `shake` and `nod` (0..1) animate a head shake ("nope") or nod ("yep").
- **Automatic life**: hover bob, seeded blinks (closed eyes become clean lines or ^ arcs), small eye darts, glow pulse, slight sway, a spark orbiting the halo, and a stand piece that lags behind the head.
- Unknown expression or pose names print a warning and fall back to the default. The rig doesn't leave any drawing settings changed.
- I added a finger-gun guard: the pointing hand always has its thumb tucked in, so it never looks like a gun.

**Layout at s=1, relative to (x, y), which is the centre of the screen-head:**

| Part | Position / size |
|---|---|
| Head | 560 x 470 (−280..280, −235..235) |
| Screen | x −246..246, y −201..185 |
| Eye centres | (±108, −36), each 128 wide x 156 tall |
| Eyebrows | about y −148 |
| Mouth centre | (0, +104) |
| Halo ring centre | (0, −306), 300 wide |
| Floating stand | (0, +286) |
| Idle hand wrists | (±316, 150) |

- Face features shift up to ±14 / ±9 px toward the look direction. The head also bobs about ±9 px and tilts slightly.
- Bounding box, measured across all poses and expressions (including hands): `BBOX = (-452, -374, 454, 386)`. `ai_bbox(x, y, s)` gives it in world coordinates. The soft glow reaches 440 px from the centre.
- `draw_ai` returns world-space points for props, emotes and bubble tails: `face`, `eyeL`, `eyeR`, `mouth`, `halo`, `top`, `handL`, `handR` (palm centres), `handL_tip`, `handR_tip`.

**Draw time** at 720x1280 (median of runs that mix every pose, talking and thinking): 6.2 ms at s=1, 5.2 ms at s=0.8, 4.1 ms at s=0.6. The back glow was originally a 5.5 ms gradient; it is now rendered once and reused.

**File size:** a 6.5 s test clip of the AI alone came out at about 189 kbps (CRF 26). That's well within the roughly 450 kbps the 15 MB limit allows for video.

**Previews** (all in `/home/user/game1/ai-video/preview/`):
- `riga_expr.png` – all 13 expressions, labelled
- `riga_hands.png` – all 16 hand poses, labelled
- `riga_lips.png` – 6 expressions × 5 mouth values
- `riga_blend.png` – neutral→unimpressed and idle→stop transitions
- `riga_roll.png` – eyeroll sequence over `t`
- `riga_blink.png`, `riga_think.png` – blinks, thinking, look directions
- `riga_zoom_face.png`, `riga_zoom_hands.png` – close-ups
- `riga_small.png`, `riga_small2.png` – phone-size readability checks
- `riga_anchors.png` – mirroring, shake/nod and anchor points marked
- `riga_perf.png`, `riga_perf.mp4` – a short scripted performance

The scripts that make them are `riga_test.py` (run with no argument, `zoom`, or `bench`), `riga_anchor.py` (add `bbox` to measure the bounding box) and `riga_perf.py` (add `video` for the clip).

## Villain + Hissy rig

The villain and snake rigs are finished and rendering. A full villain-plus-snake draw takes about 10.4 ms per frame at 720x1280 (median; best 9.7 ms), under the 12 ms target. The villain alone takes about 7 ms. I did four render, review and fix rounds and looked at every preview PNG.

**Files**
- `/home/user/game1/ai-video/engine/villain.py`
- `/home/user/game1/ai-video/engine/snake.py`
- `/home/user/game1/ai-video/preview/rigv_test.py`. Run it as `python3 preview/rigv_test.py [expr faces arms hands mouth blend anim snake snake_on full timing]`.

**Villain API**
```python
draw_villain(ctx, x, y, s, t, expr="neutral", look=(0,0), mouth=(0,0),
             arms="rest", lean=0.0, blink=None, snake=None, seed=1)
```
- **`expr`** is a name or a `(from, to, blend)` tuple from `core.state_at`. The 15 names are `neutral, smug, sneaky, evil_grin, excited, shocked, angry, frustrated, pleading, defeated, sheepish, hopeful, happy, thinking, typing_focus`. Expressions are parameter dicts blended linearly, so the eyes, lids, brows, mouth, monocle drop, vein, sweat, gloom lines and blush all morph smoothly.
- **`arms`** is a name or a tuple. The 12 names are `rest, type, steeple, rub, point, fist, facepalm, beg, shrug, chin, present, slump`. `type`, `rub`, `fist`, `beg`, `point`, `steeple` and `chin` animate with `t`. The lists are exported as `EXPRESSIONS` and `ARM_NAMES`.
- **`mouth`** is `(open, wide)` from lip-sync, or a plain float. It is layered on top of every expression's mouth: it drops the jaw and goatee, and the teeth part when he talks through the evil grin or the angry teeth.
- **`look`** moves the pupils, and the face features slide up to ±9 px toward the look direction.
- **`lean`** rotates the whole body around the waist, in radians.
- **`blink`** overrides the automatic blink (0 open, 1 closed). Closed lids meet about 60% of the way down the eye with a lash line.
- **`snake`** is `None` or a dict with keys `expr`, `look` (default `(0.3, 0)`), `mouth` (float or tuple), `tongue` and `blink`. It draws Hissy coiled behind the neck, over the right shoulder and across the chest, with the head peeking at screen-left.
- **Automatic life:** seeded blinks, breathing bob, step-like eye micro-saccades, a slow head drift, a head bob while talking, and a monocle glint sweep with a sparkle roughly every 4.6 s. The pleading expression flutters the lids and shows lashes.
- **Unknown names** print a one-time warning to stderr and fall back to `neutral`, `rest` or `idle`.

**Snake API**
```python
draw_snake_head(ctx, x, y, s, t, expr="idle", look=(0,0), mouth=0.0, tongue=None,
                blink=None, tail_from=None, seed=5, flip=False, neck=True)
```
- **`expr`** names: `idle, smug, shocked, worried, side_eye, unimpressed, happy, nod, facepalm`, or a tuple.
- **`nod`** bobs the head at 1.6 Hz. **`facepalm`** brings the tail up over both eyes; it rises out of the neck when drawn on its own and out of the coil's end when on the villain.
- **`tongue`**: `None` gives automatic flicks, `True` flicks continuously, `False` never shows it, and a float holds it at that extension.
- **`neck=True`** draws a neck stub hanging down from the head for use on its own; the villain rig passes `False`.
- **`flip`** mirrors the head horizontally.

**Anchors at s=1, relative to (x, y), with y negative upward.** Call `villain.anchors(x, y, s)` for world-space points. These ignore the expression's head offset (−18 to +24 px), head tilt (up to 0.12 rad) and lean.
- Face origin, the centre of the eye line, is `FACE = (0, −518)`.
- Eye centres are `EYES = (−62, −522)` on screen-left and `(+62, −522)` on screen-right; the screen-right eye wears the monocle. The eye radii are 37×45, and 7% bigger for the monocle eye.
- Other points:

| Point | Position |
|---|---|
| Brow line | (0, −593) |
| Mouth | (0, −388) |
| Top of dome | (0, −735) |
| Spot on the dome for emotes | (70, −678) |
| Temples | (±150, −628) |
| Above the head | (0, −800) |
| Chest | (0, −200) |
| Resting hands | (±130, −10) |

- The snake head centre is `SNAKE_HEAD = (−306, −474)`, drawn at scale 0.98·s. Its eyes are at the head centre plus (±40, −18)·0.98.

**Bounding box at s=1, relative to (x, y)**

| Pose | x range | y range |
|---|---|---|
| Most poses | −331 to +330 | −738 to +153 |
| With the snake | from −397 | |
| `shocked` (hair stands up) | | top at −763 |
| `point` | to +462 | |
| `fist` | to +356 | |
| `shrug` | ±488 | |
| `present` | to −535 | |
| Snake head alone | ±93 | −67 to +76 |
| Snake head, `shocked` | ±90 | −90 to +88 |
| Snake neck stub / tongue | | down to +241 / +118 |

The part of the villain below y=0, down to +153, is cut-off suit and cape that a desk should cover. The `present` and `shrug` hands can reach the right-hand platform UI zone if the villain is centred, so scenes should place him with that in mind.

**Preview PNGs**, all in `/home/user/game1/ai-video/preview/`:
- `rigv_expr.png`: all 15 expressions at phone-like scale.
- `rigv_faces.png`: face close-ups.
- `rigv_arms.png`: every arm pose, with `type`, `rub`, `fist` and `beg` at three times.
- `rigv_hands.png`: glove close-ups.
- `rigv_mouth.png`: 8 expressions × 5 open/wide values.
- `rigv_blend.png`: smug to shocked, rest to facepalm and sneaky to pleading, each at blend 0, .25, .5, .75 and 1.
- `rigv_anim.png`: the automatic life from 0 to 4.75 s.
- `rigv_snake.png`: Hissy's expression sheet.
- `rigv_snake_on.png`: Hissy on the villain's shoulders.
- `rigv_full.png`: one real 720x1280 frame.
- `rigv_edge.png`: edge cases (lean, s=0.35, tuple blends, unknown names, `flip`, and the anchor points marked).

## Props + backgrounds

# props.py: shared backgrounds and props, done

`/home/user/game1/ai-video/engine/props.py` implements everything in SPEC §3 with the exact names and signatures, plus the extras you asked for and a few more. Every frame cost is under 5.2 ms at 720x1280; the backgrounds take about 1–3 ms.

I ran four art-director rounds on the preview sheets and fixed:
- the moon hidden behind the rose window;
- stray slash marks on the window surround;
- an inverted floor grid on the AI background;
- the unmask tag covering the line of text above it;
- a hole showing in the wall before the service window appeared;
- the anger emote, which read as a star instead of 💢;
- clipped puzzle and folder labels;
- a weak back-view monitor;
- a stray path that was turning the snake emblem into a blob.

## Conventions
- **Coordinates:** logical 1080x1920. `t` is scene seconds. Before `t_in` / `t0`, nothing is drawn, but layout values are still returned.
- **Anchors:** rect-like props anchor at the top-left, small props at the centre, things that sit on a surface at the bottom-centre. `s` is a uniform scale.
- **Colours:** any PAL name, extra `COL` name (`wood`, `gold`, `parch`, `cork`, `steel`…) or `#hex` (use `props.C(name)`).
- **Style:** ink outlines are 5 px.
- **Background caching:** static layers are cached per device scale, read from `ctx.get_matrix()`. A camera push-in renders a new cache with 25% headroom; zoom-outs work because the cache extends past the frame edges.

## Backgrounds
| Function | Notes |
|---|---|
| `lair_bg(ctx, t, flash=0, rain=True, candle=True, bubbles=True, bolt_seed=0)` | Gothic window on the left (x 44–406, y 194–930, candle on the sill), crimson snake banner top-centre (x 438–642, y 104–470), EVIL PLANS corkboard on the right (x 694–1040, y 160–590), potion shelf at y≈760, floor from y=1400. `flash` 0..1 brightens the sky, shows a bolt above 0.35 and washes the room; for a full hit, also call `flash(ctx, 0.2*f)` after drawing characters. Only rain, the candle and the flask bubbles move. |
| `ai_bg(ctx, t, motes=10, floor=True)` | Navy with a centre glow at (540, 820), faint dot grid, two faint rings around the AI, a perspective grid floor below y=1330, and up to 12 slow motes. |

## Lair props
| Function | Notes |
|---|---|
| `desk(ctx, x, y, w, lamp=True, emblem=True, h=None)` | (x, y) is the front-top edge, which equals the villain's waist y. Typical w is 860–1100. The top surface is drawn 34 px above y; the front runs to the bottom of the frame. `lamp=True` puts the skull lamp on the left end; a float gives its x offset. |
| `computer(ctx, x, y, s=1, screen_fn=None, view="front"/"side"/"back", facing=1, glow=1, t=0, label="EVILTRON")` | (x, y) is the bottom-centre. At s=1 it is about 440x440 and the screen is 368x266. `screen_fn(ctx, sw, sh)` draws in screen-local px and is clipped to the screen. "side" casts a teal light wedge toward `facing`, which reads as lighting his face. Returns `{"screen": rect, "glow": (x, y)}`. |
| `keyboard(ctx, x, y, w=380, t, typing=False)` | (x, y) is the centre of its front edge. |
| `mug(ctx, x, y, s, txt="#1 EVIL", t=None)` | Bottom-centre anchor; `t` adds steam. |
| `skull_lamp(ctx, x, y, s, on=1)` | Bottom-centre anchor. |

## Chat
**`chat_bubble(ctx, x, y, w, txt, who, t, t_in, highlight=None, font_size=40, fit=True, reveal=None, t_out=None)`**
- (x, y, w) is the top-left of a column of width w (typically 640–820).
- The bubble hugs its text. "villain" is purple, right-aligned, tail bottom-right; "ai" is teal, left-aligned, tail bottom-left; "narrator" is a dark panel, centred, no tail.
- It pops in from the tail tip over 0.32 s.
- It returns a `BubbleLayout`, which is a float equal to the height including the tail. Stack the next bubble with `y += h + gap`. It also carries `.rect`, `.tail`, `.spans`, `.lines` and `.tag_space` (= 1.9*font_size).

**`highlight` entries:**
- Each entry is a `str`, a `(str, t0)` tuple, or a dict: `{"text", "t0", "style": underline|box|fill|strike, "color": "warn", "unmask_t", "tag", "unmask_color": "danger", "tag_pos": auto|above|below, "all": True}`.
- Matching is case-insensitive and marks every occurrence, across line wraps too.
- At `unmask_t` the marker turns red, becomes a box, the words get a red tint, and the tag chip pops up outside the bubble with a leader line to the words. Leave `tag_space` free above or below the bubble.
- `bubble_layout(...)` gives the same layout without drawing.

**`typing_dots(ctx, x, y, t, who, t_in=None, s=1)`** – (x, y) is the top-left; the bubble is about 150x80. Returns (w, h).

## Wall and stamp
**`brick_wall(ctx, x, y, w, h, t, t0, rows=6, window=None, label=None, speed=1, drop=380, seed=0)`**
- (x, y) is the top-left of the finished wall; typical size is 760x560.
- Bricks are about 2:1 and build bottom row first: a row every 0.16 s, bricks 0.035 s apart. Each one falls, squashes and bounces twice with a dust puff on landing, and mortar fills in behind finished rows.
- Six rows finish about 1.45 s after `t0` (divided by `speed`).
- `window` is `(wx, wy, ww, wh)` relative to the wall's top-left, or a dict `{"rect", "t_open" (shutter rolls up then), "fill" (None = see-through), "awning": True, "sign": "OPEN"}`. The frame, counter and striped awning pop in first, and the wall builds around them.
- `label` is a str or `{"text", "color", "size", "y"}`. It wipes on after completion and auto-fits the free band above or below the window.
- Returns `{"t_done", "land_times", "window": world rect, "rect"}`.
- For sound effects, `brick_wall_land_times(t0, rows, speed)` gives the row landing times without a ctx.

**`stamp(ctx, x, y, txt, t, t_in, color="danger", size=1, rot=-0.12, t_out=None, font="black")`**
- (x, y) is the centre; text is 110 px at size 1.
- It drops from 2.3x with a twist, hits at `stamp_impact(t_in)` (= t_in + 0.11), springs back with overshoot, and impact ticks burst out.
- A "✓" or "✗" in the text is drawn as a vector mark.

## Vision
**`future_tree(ctx, x, y, s, t, t0, branches, direction="down"|"right", step=0.55, judge=None, root_label=None, spread=None, level=None, label_size=32)`**
- (x, y) is the root centre. Levels are 250*s apart; leaves spread over min(880, leaves*220*s).
- Each node is a dict: `{"label", "kind": "harm"|"safe"|"neutral" (inherits from the parent), "icon": bomb|heart|book|gift|star|skull|people|bulb|question, "children": [...], "t", "judge"}`.
- Everything grows in cyan first, with a spark at each growing path tip.
- At the verdict time (default: show time + 0.5 s, or the global `judge` time staggered by depth), harm nodes turn red, shake, get an X and a dashed red path. Safe nodes turn green with a ring pulse and a check badge.
- Returns the node list (world x/y and times); `future_tree_layout(...)` gives it without drawing.

**`scroll_doc(ctx, x, y, w, h, title, lines, t, t_in, font_size=34, unroll=0.6, line_gap=0.22)`**
- (x, y) is the top-left of the paper; typical size is 700x900.
- It unrolls, then the lines slide in one by one.
- Line items: a plain str, `{"text", "color", "size"}`, `{"redact": "the recipe stays off the page"}` (a mini brick strip with a caption chip), or `{"gap": px}`.

## Reactions and screen helpers
- **`emote(ctx, kind, x, y, s, t, t_in, t_out=None)`** – centre anchor, about 110 px. Kinds: sweat, anger (💢), question, exclaim, sparkle, heart, lightbulb, zzz.
- **`sparkles(ctx, x, y, r, t, n=6, seed=0, color="white", size=1)`** – twinkling stars within radius r.
- **`x_mark(ctx, x, y, s, t, t_in)`** and **`check_mark(...)`** – about 140 px at s=1; they swipe in over about 0.24 s.
- **`label_tag(ctx, x, y, txt, color="warn", size=30, text_color=None, t=None, t_in=None, font="ui", pointer=None|"down"|"up", rot=0)`** – centre anchor; returns (w, h).
- **`arrow(ctx, x0, y0, x1, y1, color="warn", t_progress, bend=0.18, width=14, head=1)`**
- **`split_divider(ctx, y, t, top="bubble_villain", bottom="ai_rim", badge=None)`** – a 24 px band with purple glow above and cyan below, plus a gliding light pulse.
- **`split_screen(ctx, t, top_fn, bottom_fn, y=900, top_view=None, bottom_view=None, badge=None)`** and **`panel(ctx, x, y, w, h, draw_fn, view=(vx, vy, vw), radius=0, border=True)`** – `draw_fn(ctx)` draws in normal frame coordinates; `view` picks the source region. For example, `top_view=(-150, 380, 1380)` shrinks the top shot so a whole character fits.
- **`iris(ctx, t, t0, t1, cx=540, cy=820, closing=True, color="black", ring="ai_accent")`**
- **`flash(ctx, a, color="white")`**
- **`title_card(ctx, t, t_in, line1, line2=None, y=800, color="ai_accent", color2="white", size=None, burst=False, t_out=None, burst_color="ai_rim")`** – letters drop in one at a time and then hold still.
- **Extras:**
  - `cartoon_bomb(ctx, x, y, s, t, lit=True)` – ball r=60.
  - `magnifier(ctx, x, y, s, rot=0.6)` – lens r=70.
  - `puzzle_piece(ctx, x, y, s, color, label, rot, tabs=(top, right, bottom, left))` – 160 px body; label auto-fits.
  - `folder(ctx, x, y, s, label, color, stamp_txt)` – 300x220.
- **Misc:** `C(name)`, `clear_cache()`.

## Draw times (ms per frame at 720x1280)
| Function | ms |
|---|---|
| lair_bg | 1.0–2.5 |
| lair_bg with flash | 1.9–3.1 |
| ai_bg | 0.8–1.9 |
| desk + lamp | 2.8 |
| computer (front) | 3.9 |
| chat_bubble with highlights | 1.6 |
| brick_wall (animating / finished with window and label) | 2.3 / 5.1 |
| future_tree | 3.7 |
| stamp | 1.5 |
| scroll_doc | 2.6 |

- The one-off cache build on each worker's first frame is 56 ms (lair) and 45 ms (AI background).
- In 6 s test encodes (veryslow, CRF 27): the static lair is about 64 kbps, the full lair with rain, candle and bubbles about 87 kbps, and the AI background with motes about 45 kbps. `rain=False` saves about 20 kbps.

## Files
- `/home/user/game1/ai-video/engine/props.py` (the module)
- `/home/user/game1/ai-video/preview/props_test.py` (`python3 preview/props_test.py [sheet…|timing]`)
- `/home/user/game1/ai-video/preview/props_motion.py` (24 fps frame strips)

Preview sheets:
- `/home/user/game1/ai-video/preview/props_backgrounds.png`
- `/home/user/game1/ai-video/preview/props_detail.png`
- `/home/user/game1/ai-video/preview/props_bubbles.png`
- `/home/user/game1/ai-video/preview/props_wall.png`
- `/home/user/game1/ai-video/preview/props_stamp.png`
- `/home/user/game1/ai-video/preview/props_emotes.png`
- `/home/user/game1/ai-video/preview/props_tree.png`
- `/home/user/game1/ai-video/preview/props_scroll.png`
- `/home/user/game1/ai-video/preview/props_misc.png`
- `/home/user/game1/ai-video/preview/props_motion.png`

## Audio (music, SFX, mixer)

I built the music, the sound effects and the final mixer. Everything renders, `python3 build.py audio` writes `out/mix.wav`, and every numeric check passed. Nobody has listened to it yet, though: musical quality is checked only by measurements and by reading the spectrograms.

**What other code calls**
- `audio/music.py`: `render_cue(name, dur, sr=48000, fade_in=0.02, fade_out=1.0, seed=0)` returns float32 of shape (round(dur·sr), 2).
  - Each cue is an 8-bar loop that repeats with small variations, so it works at any length; the last 1 s fades out. `'none'` and unknown cue names return silence.
  - Every render is normalized to -18 LUFS, with peaks soft-limited to about -1 dBFS.
  - The first half of the file is a shared DSP toolkit that `sfx.py` and `mix.py` reuse.
- `audio/sfx.py`: `render(name, sr=48000, seed=0)` returns float32 (n, 2) with peaks at about -12 dBFS.
  - `NAMES` lists 37 effects. `resolve()` also accepts aliases and loose spellings: "thud", "ding", "boom", "hiss", "pop2", "sfx_whoosh", "Brick Thud" all work. Unknown names raise `KeyError`.
  - `seed` (0–3) gives small variations so repeated sounds aren't identical.
- `audio/mix.py`: `run()` writes `out/mix.wav` (48 kHz stereo, 16-bit, dithered) and returns the path. Optional arguments: `timeline_path`, `out_path`, `lines_dir`, `sfx_override`, `stems_dir`, `procs=4`. `run.report` holds the numbers below.

**How the mix behaves**
- **Scene timing:** scenes are placed where the video actually puts them (each scene rounded to whole frames), not at the unrounded timeline start. Without this, lip-sync would drift by a frame or more over many scenes.
- **Music:** consecutive scenes with the same cue are rendered as one continuous piece. Different cues crossfade over 0.6 s, and renders run on 4 processes.
- **Music level:** the bed sits 13 dB under the dialogue and drops 6 dB more while anyone speaks (80 ms attack, 400 ms release). It starts dropping 120 ms before each line so first syllables aren't masked.
- **Two additions you didn't ask for:**
  - Music rises 3 dB in stretches with no dialogue for more than about a second.
  - Each voice line gets a de-esser and peak control, so the master limiter only works lightly.

**Settings scene authors can use** (other agents need to be told these exist):
- Scene fields in `script.json`: `music`, `music_gain` (dB), `music_xfade` (seconds for the cut into that scene, e.g. 0.05 for a hard cut), `music_restart`.
- Line fields: `gain` (dB) and `dry` (skip reverb/chorus). Every line is levelled to the same loudness, so a shout or whisper needs `gain` to stand out.
- `SFX(info)` returns `(t, name, gain_db[, pan])` in scene-local seconds; negative `t` is allowed.
- Unknown effect names and scene modules that don't exist yet are warned about and skipped.

**Voices:** high-pass filter, gentle 3:1 compression, de-esser, and a small mud cut plus presence boost for phone speakers. The villain gets a little stone-room reverb (-17 dB), the AI a subtle chorus with a faint bright shimmer, and the narrator is nearly dry.

**Cues**
| Cue | Key / tempo | What it is | Chords |
|---|---|---|---|
| doom | D minor, 70 BPM | trailer-parody brass "BRAAAM"s, booms, taiko, choir, drone, soft clock tick | Dm–Bb–C–A, two bars each |
| sneaky | A minor, 104 BPM | pizzicato bass with chromatic walk-ups, staccato plucks, bassoon doubling, woodblock | Am Am Dm Am F E7 Am E7 |
| ai_calm | C lydian, 90 BPM | warm pads, electric-piano arpeggios, bells, light percussion | Cmaj7 D/C Em7 Am7 Fmaj7 G6 C/E D/F# |
| tension | A minor, 110 BPM | 16th-note synth pulse with a filter rising every 4 bars, "computing" blips, pumping pad | Am Am Fmaj7 Fmaj7 Dm7 Dm7 Esus4 E |
| beg | D minor, 66 BPM | melodramatic strings that swell, sobbing violin with slides and heavy vibrato, timpani rolls, harp glissando | Dm Gm Bb A7 Dm Gm Eb A7 |
| heart | G major, 72 BPM | soft piano chords and broken bass, melody enters on the second pass, gentle pad | G D/F# Em7 Cadd9 G/B C Am7 Dsus4–D |
| resolve | D major, 96 BPM | bells and pads, then drums, then lead melody and strings, then open hats and tom fill — layers enter across the cue's own length | D A/C# Bm7 G D/F# G Em7 Asus4–A |

**Effects (37):** all 33 you asked for — key_clack, typing, send, receive, pop, brick_thud, whoosh, swoosh_up, record_scratch, thunder, sparkle, buzzer_nope, stamp, snake_hiss, boing, sad_trombone, dun_dun_dun, ta_da, glitch, heartbeat, paper, gulp, idea_ding, boom_cartoon, laser, robot_stomp, magic_chime, crowd_aww, crowd_laugh, page_flip, puzzle_click, scan_beep, power_down — plus 4 extras: drumroll, tiptoe, tick, riser.

**Verification** (`python3 preview/audio_test.py`, log in `preview/audio_test_log.txt`)
- **Music, 20 s per cue:** every cue measured -18.0 to -18.1 LUFS with peaks between -7.1 and -2.9 dBFS.
  - No NaN, no DC offset (largest 3e-6), and zero clicks.
  - Energy above 8 kHz is 40–70 dB below the total. I darkened `sneaky` from -19 dB, and moved weight from sub-bass to mids in doom/ai_calm/tension/resolve so they hold up on phone speakers.
- **Harmony:** every chord voicing uses only chord tones.
  - Melody notes land on chord tones 83–95% of the time; sneaky (65%) and ai_calm (67%) are lower by design (chromatic sneaking, added 9ths).
  - In the rendered audio, 0.71–0.84 of the pitch energy sits on the intended chord, against about 0.30 for random. Sneaky scores lowest at 0.50 (its bass is below the 80 Hz analysis floor, and it has chromatic passing notes).
  - Instruments are in tune within ±2 cents.
- **Spectrograms:** I looked at all seven. They show the bar structure, the chord changes, tension's filter sweeps, beg's violin slides and vibrato, and resolve's layers building. There's no noise wash; doom has only a faint high noise floor about 55 dB down.
- **Effects:** all 37 pass. The click detector found three hard truncations and some sharp onsets, now fixed. Edges are 0, DC under 4e-4, and the effects contact sheet looks right. crowd_laugh pulses at 4.6 Hz like real laughter; crowd_aww's vowel falls from "ah" to "aw".
- **Mix test (65 s fake timeline, 8 cues):** -14.01 LUFS (ffmpeg also measures -14.0), true peak -1.5 dBTP (ffmpeg agrees).
  - Bus compressor works at most 0.4 dB and the limiter 2.2 dB.
  - Music is 18.8 dB under dialogue while talking; the ducking is already 78% in at every line start.
  - Crossfades have no dropouts; missing scene modules and unknown effect names were skipped with warnings.
- **Speed (4.5-minute fake timeline, 33 scenes):** the whole mix took 45–56 s, of which music was about 7–15 s on 4 CPUs (about 23 s single-threaded). That is inside the 60 s budget.
- **Real run:** `python3 build.py audio` on the current one-scene test timeline works (-14.0 LUFS, -2.0 dBTP).

The true-peak ceiling is -1.5 dBTP so the AAC encode in `build.py final` should stay under -1, but I haven't measured the encoded file.

Files are in /home/user/game1/ai-video:
- audio/music.py
- audio/sfx.py
- audio/mix.py
- preview/audio_test.py

The test writes its output into preview/: `audio_music_<cue>.wav`, `audio_sfx_<name>.wav`, `audio_spec_<cue>.png`, `audio_spec_sfx.png`, `audio_mix_test.wav` and `audio_spec_mixtest.png`.