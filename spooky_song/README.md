# Clickety-Clack! — a moonlight bone dance

An original ~2:22 Halloween song as a portrait (1080×1920) animated video,
starring Alice the little ghost (from Alice's drawing), Granny Simmer the
cauldron, and a new friend: **Mister Marrow**, a jolly skeleton bandleader in a
crooked purple bowler, with his Moonlight Bone Crew, a pumpkin drummer, a black
cat on the fiddle and a bat on a tiny horn.

**Output:** `clickety_clack.mp4` (H.264 + AAC, karaoke lyrics burned in, first
frame is the titled scene) and `clickety_clack.srt` (lyrics + dialogue).

## The song

Everything — lyrics, melody, arrangement — is original, written for this video
in the spirit of a bouncy spooky-skeleton novelty song (no existing song's words
or tune are used).

| Part | What happens |
|---|---|
| Intro | Midnight bells. Alice wanders into the graveyard; a skull peeks from a grave: *"Psst. Hey… you. Yes, you. It's midnight."* |
| Verse 1 | Marrow climbs out and sings; the crew follows — dust off ribs, polish toes, *tap, tap, tap*. Alice hides behind a tombstone. |
| Chorus | *Clickety-clack, the bones come back, the moon is up and the night is black!* — synchronized bone dance |
| Verse 2 | Meet the band: Granny Simmer bubbling by the gate, the pumpkin drummer, the cat, the bat. Alice drifts out, tapping along. |
| Chorus 2 | Marrow beckons; Alice joins the dance. |
| Stop | The band stops dead: *"Your turn, little ghost! Give us a clack!"* … *pff.* … crickets. |
| Bridge | *"I don't have any bones. I can't clickety… and I can't clack."* — *"Nobody here sounds the same… so what does a ghost go?"* — *"…boo?"* — *"Louder!"* |
| BOO | Alice's big BOO blows everyone's hats off; the song jumps up a key. |
| Final chorus | *Bones go clack and the pot goes pop, and a little ghost goes BOO at the top!* |
| Tag | *Everybody's got a sound of their own, so sing it out loud — you were never alone!* |

## How it's made (all generated in code)

| Step | File | What it does |
|---|---|---|
| Song | `song.py` | Lyrics, melody (syllable/MIDI/eighths), form, who sings what, dialogue |
| Singing | `sing.py` | Kokoro TTS speaks each line, then the WORLD vocoder re-times every syllable onto its note and replaces the pitch with the melody (glides, vibrato) — one consistent voice per character for singing and talking; lip/jaw data |
| Band | `music.py`, `synth.py` | Synthesized xylophone, tuba oom-pah, castanet bone-clacks, drums, organ, fiddle, muted horn, choir, bells; stingers in the bridge; mix |
| Picture | `render.py`, `skeleton.py`, `scene.py`, `drawkit.py` | Cairo vector animation: rigged skeletons with a dance vocabulary keyed to the beat, expressive skull faces and flapping jaws, Alice and Simmer from the first short, the band, karaoke lyrics |
| Encode | `encode.py` | Loudness normalize (−15 LUFS), two-pass H.264 sized to fit |

Rebuild with `./build.sh` (optional target size in MB, default 14.2). Stills:
`python render.py --still 24 104`. Quality check: `python encode.py --check`.

Easy things to change: words and notes in `song.py` (keep each phrase's
syllable count matching its notes); choreography and camera shots in
`render.direct()`; dance moves in `skeleton.dance()`.
