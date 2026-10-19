# Alice — a little ghost who can't keep a single snack

A ~3-minute portrait (1080×1920) animated short grown from Alice's drawing
(`assets/original_drawing.jpg`): the ghost with tall oval eyes and mouth, the
three-lobed hem with little foot dots, the thought bubbles ("eat yum!"), the
eyeball and stripey sweets, the smiling cauldron with three rings on its rim,
and the two hearts — one hollow, one filled.

**Output:** `alice.mp4` (H.264 + AAC, burned-in subtitles, opens on a full
scene with the title — no fade from black) and `alice.srt` (same captions,
for platforms that take a caption upload).

## The story

A rhyming storybook narrator introduces Alice, a small ghost in a crooked
gothic town who dreams about snacks — but everything she eats falls straight
through her. Granny Simmer, a spectacled old cauldron, notices the sweets
rolling under her belly, and Alice admits the hunger is really a hollow feeling:
at the town's Moon Supper she is "there… but not really there." Simmer's
answer — *nobody remembers the soup, they remember who was sitting next to
them* — becomes a see-through soup: the sweets turn into steam, steam is
"soup that's learned how to float," and Alice can finally taste it. The hollow
heart on her chest fills in, and at the Moon Supper she has a seat next to a
friend.

Style: a spooky-sweet gothic storybook look — huge moon, curly spiral-tipped
trees, crooked houses, striped wallpaper and cloths, diamond floors, black ink
outlines with a slight stop-motion "boil" — built from generic shapes, with no
characters, names, songs or symbols from any existing film.

## How it's made (all generated in code)

| Step | File | What it does |
|---|---|---|
| Script | `story.py` | Beats, lines, emotions, gaze, word-timed cues, stingers |
| Voices | `voice.py` | Kokoro TTS (narrator `bm_fable`, Alice `af_heart` pitched up, Simmer `bf_emma` pitched down with a warble) |
| Timing | `timeline.py` | Word-level timings → subtitles, reactions, stingers |
| Sound | `audio.py` | Original D-minor waltz (celesta, pizzicato, tuba, choir, theremin) that turns to D major once she tastes the steam; high twinkles on hopeful words, low swells on heavy ones; synthesized SFX; ducking; lip-sync data |
| Picture | `render.py` | Cairo vector animation: emotions blended per character (brows, lids, eye size, glints/gaze, mouth shape from the voice, blush, tear, arms, squash, lean), blinks, listener nods |
| Encode | `encode.py` | Two-pass loudness normalize (−15 LUFS) and H.264 encode |

Rebuild everything with `./build.sh` (optionally pass a target size in MB,
e.g. `./build.sh 20`; default 14.2). `python encode.py --check` reports SSIM/PSNR
against the lossless render — the shipped file measures SSIM 0.996, PSNR 47.8 dB
at 14.2 MB. Stills for checking a moment: `python render.py --still 12.5 80`.

Easy things to change: lines and emotions in `story.py`; voices and pitch in
`story.VOICES`; music sections and stingers in `audio.py`; colours and layout
near the top of each `bg_*` function in `render.py`.

Fonts (OFL / Apache, in `assets/fonts`): Mountains of Christmas, Patrick Hand,
Schoolbell, Sniglet.
